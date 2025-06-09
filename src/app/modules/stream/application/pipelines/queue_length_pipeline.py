from typing import Final
import asyncio
from datetime import datetime

import cv2
import numpy as np
import openvino as ov


class QueueLengthPipeline:
    """
    Пайплайн для определения количество людей в очереди.
    """

    PERSON_CLASS: Final[int] = 0
    DEVICE: Final[str] = "CPU"

    def __init__(
        self,
        model_path: str,
        conf_threshold: float = 0.25,
        input_size: int = 640,
        jobs_count: int = 4,
        roi: np.ndarray | None = None,
    ) -> None:
        """
        Args:
            model_path: Путь к файлу `.xml` модели.
            conf_threshold: Минимальный score бокса для принятия.
            input_size: Размерность входного изображения.
            jobs_count:  Количество параллельных запросов очереди.
            roi: Полигон зоны интереса.
        """
        self.conf_threshold = conf_threshold
        self.input_size = input_size
        self.roi = roi
        self.last_vis_frame: np.ndarray | None = None

        # Создаём runtime и компилируем модель
        self.core: ov.Core = ov.Core()
        model_ir: ov.Model = self.core.read_model(str(model_path))
        # Делаем batch динамическим, удерживая 3×H×W фиксированными
        model_ir.reshape({0: ov.PartialShape([-1, 3, input_size, input_size])})
        self.compiled: ov.CompiledModel = self.core.compile_model(model_ir, self.DEVICE)
        self.inp, self.out = self.compiled.input(0), self.compiled.output(0)

        # Настраиваем очередь
        self.queue = ov.AsyncInferQueue(self.compiled, jobs=jobs_count)
        self.queue.set_callback(self._on_complete)

    def _resize_letterbox(
        self,
        img: np.ndarray,
        color: int = 114,
    ) -> (np.ndarray, float, int, int):
        """
        Масштабирует изображение с сохранением пропорций и дополняет
        свободное пространство до квадрата необходимой размерности.

        Args:
            img: Оригинальный кадр.
            color: Цвет заливки отступа (свободного поля). 114 — среднесерый (по всем трём каналам одинаково).

        Returns:
            *out* – Готовый квадрат input_size × input_size с картинкой по центру и полями цвета color по краям;
            *scale* – масштаб длинной стороны (Во сколько умножили (или поделили) длинную сторону, чтобы она стала ровно input_size);
            *pad_t, pad_l* – верхний и левый отступы (сколько пикселей пустого поля добавили сверху (Top) и слева (Left), чтобы выровнять картинку по центру квадрата).
        """
        h0, w0 = img.shape[:2]
        scale = self.input_size / max(h0, w0)
        nh, nw = int(round(h0 * scale)), int(round(w0 * scale))
        pad_t, pad_l = (self.input_size - nh) // 2, (self.input_size - nw) // 2
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
        out = cv2.copyMakeBorder(
            resized,
            pad_t,
            self.input_size - nh - pad_t,
            pad_l,
            self.input_size - nw - pad_l,
            cv2.BORDER_CONSTANT,
            value=(color,) * 3,
        )
        return out, scale, pad_t, pad_l

    @staticmethod
    def _convert_bgr_to_rgb(img: np.ndarray) -> np.ndarray:
        """
        Преобразует изображение из цветового пространства BGR в RGB.

        В OpenCV кадры читаются в порядке каналов *Blue–Green–Red*. Большинство
        нейросетевых моделей, включая YOLO-v5/8/11, обучены на *Red–Green–Blue*,
        поэтому перед инференсом требуется переставить каналы.
        """
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    @staticmethod
    def _hwc_to_chw(img: np.ndarray) -> np.ndarray:
        """
        Меняет порядок осей с HWC на CHW.

        Большинство фреймворков глубокого обучения (PyTorch, ONNX, OpenVINO)
        ожидают макет «*Channel × Height × Width*». OpenCV же отдаёт массивы
        в форме «*Height × Width × Channel*».
        """
        return img.transpose(2, 0, 1)

    @staticmethod
    def _normalize(img: np.ndarray) -> np.ndarray:
        """
        Приводит значения пикселей к диапазону "[0, 1]" и типу "float32".

        Большинство современных YOLO-моделей обучались на входах,
        нормализованных делением на 255. Без этого веса сети будут
        интерпретировать пиксели неправильно и метрики резко упадут.
        """
        return (img / 255.0).astype(np.float32)

    @staticmethod
    def _add_batch(img: np.ndarray) -> np.ndarray:
        """
        Добавляет ведущую ось *batch* со значением 1.
        """
        return img[None]

    def preprocess(self, frame: np.ndarray) -> (np.ndarray, float, int, int):
        """
        Полная предобработка кадра.

        Args:
            frame: Входной кадр.

        Returns:
            "tensor" ("1×3×S×S" FP32 RGB‑CHW) + параметры letterbox.
        """
        img, sc, pt, pl = self._resize_letterbox(frame)
        img = self._convert_bgr_to_rgb(img)
        img = self._hwc_to_chw(img)
        img = self._normalize(img)
        img = self._add_batch(img)
        return img, sc, pt, pl

    @staticmethod
    def _iou(box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
        """
        Считает перекрытие (Intersection-over-Union) одного бокса с пачкой других.
        """
        ix1 = np.maximum(boxes[:, 0], box[0])
        iy1 = np.maximum(boxes[:, 1], box[1])
        ix2 = np.minimum(boxes[:, 2], box[2])
        iy2 = np.minimum(boxes[:, 3], box[3])
        inter = np.clip(ix2 - ix1, 0, None) * np.clip(iy2 - iy1, 0, None)
        union = (
            (box[2] - box[0]) * (box[3] - box[1])
            + (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
            - inter
        )
        return inter / (union + 1e-6)

    def _nms(
        self, boxes: np.ndarray, scores: np.ndarray, iou_thr: float = 0.45
    ) -> list[int]:
        """
        Выполняет одно-классную Non-Max Suppression (NMS).

        Алгоритм проходит по боксам в порядке убывания **scores** и
        отбрасывает все последующие боксы, у которых IoU с уже выбранным
        больше порога "iou_thr".
        """
        order = scores.argsort()[::-1]
        keep = []
        while order.size:
            i = int(order[0])
            keep.append(i)
            if order.size == 1:
                break
            order = order[1:][self._iou(boxes[i], boxes[order[1:]]) < iou_thr]
        return keep

    def _inside_roi(self, x: float, y: float) -> bool:
        """True, если точка (x, y) лежит в ROI-полигоне или ROI отсутствует."""
        if self.roi is None:
            return True
        return cv2.pointPolygonTest(self.roi, (x, y), False) > 0

    def _on_complete(
        self,
        req: ov.InferRequest,
        userdata: tuple[asyncio.Future[int], float, int, int],
    ) -> None:
        fut, sc, pt, pl = userdata
        raw = req.get_output_tensor(self.out.index).data
        boxes, _ = self.postprocess(raw, sc, pt, pl)
        # Пробуждаем asyncio-loop и кладём результат
        asyncio.get_event_loop().call_soon_threadsafe(fut.set_result, len(boxes))

    def postprocess(
        self,
        raw: np.ndarray,
        sc: float,
        pt: int,
        pl: int,
    ) -> (np.ndarray, np.ndarray):
        """Преобразует "сырой"»" выход модели в финальные боксы людей.

        Args:
            raw: Выходной тензор модели YOLO (любого поддерживаемого
                layout’а и точности).
            sc: Масштаб.
            pt: Количество пикселей, добавленных сверху (top padding).
            pl: Количество пикселей, добавленных слева (left padding).

        Returns:
            * **boxes** – массив "(M, 4)" с координатами рамок
              в формате "x1, y1, x2, y2" **в системе исходного кадра**.
            * **scores** – вектор доверительных оценок длиной "M".
        """
        pred = raw.squeeze()

        # Унифицируем форму до "(8400, 84/85)"
        if pred.shape[0] in (84, 85) and pred.shape[1] > 1000:
            pred = pred.T

        # Вычисляем скор для класса
        if pred.shape[1] == 85:
            obj, cls = pred[:, 4], pred[:, 5:]
            scores = obj * cls[:, self.PERSON_CLASS]
        elif pred.shape[1] == 84:
            cls = pred[:, 4:]
            scores = cls[:, self.PERSON_CLASS]
        else:
            raise RuntimeError(f"Unexpected output shape {pred.shape}")

        mask = scores > self.conf_threshold
        boxes, scores = pred[mask, :4], scores[mask]
        if boxes.size == 0:
            return np.empty((0, 4)), np.empty(0)

        # cx,cy,w,h -> x1,y1,x2,y2
        boxes[:, :2] -= boxes[:, 2:] / 2
        boxes[:, 2:] += boxes[:, :2]

        # Убираем паддинг и масштаб
        boxes -= np.array([pl, pt, pl, pt])
        boxes /= sc

        keep = self._nms(boxes, scores)
        boxes, scores = boxes[keep], scores[keep]

        # Фильтр по зоне интереса (ROI)
        cx = (boxes[:, 0] + boxes[:, 2]) / 2
        cy = (boxes[:, 1] + boxes[:, 3]) / 2
        roi_mask = np.array([self._inside_roi(x, y) for x, y in zip(cx, cy)])
        return boxes[roi_mask], scores[roi_mask]


    def _draw_boxes(self, frame: np.ndarray, boxes: np.ndarray) -> np.ndarray:
        """
        Копирует frame, рисует на нём ROI, все боксы и накладывает таймштамп слева сверху.
        """
        frame_vis = frame.copy()

        # Рисуем ROI (если задана)
        if self.roi is not None:
            pts = self.roi.reshape((-1, 1, 2))
            cv2.polylines(frame_vis, [pts], isClosed=True, color=(0, 0, 255), thickness=2)

        # Рисуем боксы (людей)
        for x1, y1, x2, y2 in boxes.astype(int):
            cv2.rectangle(frame_vis, (x1, y1), (x2, y2), color=(255, 0, 0), thickness=2)

        # Рисуем таймштамп
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        (w, h), _ = cv2.getTextSize(ts, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(frame_vis, (0, 0), (w + 10, h + 10), (0, 0, 0), thickness=-1)
        cv2.putText(
            frame_vis,
            ts,
            (5, h + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            thickness=1,
            lineType=cv2.LINE_AA,
        )

        return frame_vis

    async def process_async(self, frame: np.ndarray) -> int:
        """
        Асинхронно Обрабатывает кадр и возвращает количество людей.
        """
        img, sc, pt, pl = self.preprocess(frame)
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[int] = loop.create_future()
        self.queue.start_async({self.inp: img}, userdata=(fut, sc, pt, pl))
        return await fut

    def process(self, frame: np.ndarray) -> tuple[int, np.ndarray]:
        """
        Обрабатывает кадр и возвращает количество людей в зоне интереса (очереди) и обработанный кадр.
        """
        img, sc, pt, pl = self.preprocess(frame)
        raw = self.compiled({self.inp: img})[self.out]
        boxes, _ = self.postprocess(raw, sc, pt, pl)
        vis_frame = self._draw_boxes(frame, boxes)
        return len(boxes), vis_frame
