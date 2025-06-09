from datetime import time, datetime

from pydantic import BaseModel, Field, field_validator
import numpy as np


class Point(BaseModel):
    """
    Схема точки с координатами x и y.

    Attributes:
        x (int): Координата по оси X.
        y (int): Координата по оси Y.
    """

    x: int = Field(..., description="Координата по оси X")
    y: int = Field(..., description="Координата по оси Y")

    def __iter__(self):
        """
        Позволяет преобразовать np.array(point) в [x, y]
        """
        yield self.x
        yield self.y


class Polygon(BaseModel):
    """
    Схема полигона, содержащая уникальный идентификатор и список точек.

    Attributes:
        id (int): Уникальный идентификатор полигона.
        points (List[Point]): Список точек полигона.
    """

    id: int = Field(..., description="Уникальный идентификатор полигона")
    points: list[Point] = Field(..., description="Список точек полигона")

    @property
    def np(self) -> np.ndarray:
        """
        Получить полигон в формате списка numpy.
        """
        return np.array([[tuple(p)] for p in self.points], dtype=np.int32)


class ROIPolygons(BaseModel):
    """
    Схема для 'roi_polygons', представляющая список полигонов зон интереса.

    Attributes:
        polygons (List[Polygon]): Список полигонов, каждый из которых содержит уникальный ID и точки.
    """

    polygons: list[Polygon] = Field(
        ...,
        description="Список полигонов, каждый из которых содержит уникальный ID и точки",
    )

    def as_list(self) -> list[np.ndarray]:
        """
        Получить список полигонов (каждый – np.ndarray)
        """
        return [p.np for p in self.polygons]


class IndicatorsStatus(BaseModel):
    """
    Схема для `indicators_types`, указывающая какие показатели отслеживаются.

    Attributes:
        queue_length (bool): Отслеживание длины очереди.
        service_duration (bool): Отслеживание времени обслуживания клиента.
    """

    queue_length: bool = Field(..., description="Отслеживание длины очереди")
    service_duration: bool = Field(
        ..., description="Отслеживание времени обслуживания клиента"
    )


class Indicators(BaseModel):
    """
    Схема для `indicators`, хранящая значения отслеживаемых параметров или пороговые значения для них.

    Attributes:
        queue_length (int | None): Длина очереди, если отслеживается.
        service_duration (float | None): Время обслуживания клиента в секундах, если отслеживается.
    """

    queue_length: int | None = Field(
        None, description="Длина очереди, если отслеживается"
    )
    service_duration: float | None = Field(
        None, description="Время обслуживания клиента в секундах, если отслеживается"
    )


class Camera(BaseModel):
    id: int
    name: str = Field(..., max_length=120)
    preview: str | None = Field(None, max_length=255)
    url_address: str = Field(..., max_length=80)
    connection_login: str = Field(..., max_length=50)
    connection_password: str = Field(..., max_length=50)
    start_time: time | None = None
    end_time: time | None = None
    is_active: bool
    indicators_status: IndicatorsStatus
    roi_polygons: ROIPolygons

    @field_validator("roi_polygons", mode="before")
    def _build_roi_polygons(cls, v):
        if isinstance(v, list):
            polygons: list[Polygon] = []
            for idx, poly_pts in enumerate(v, start=1):
                pts = [Point(**pt) for pt in poly_pts]
                polygons.append(Polygon(id=idx, points=pts))
            return ROIPolygons(polygons=polygons)

        return v


class Record(BaseModel):
    camera: int = Field(..., description="ID камеры")
    record_time: datetime = Field(..., description="Момент фиксации (UTC)")
    indicators_value: Indicators = Field(
        ..., description="Значения рассчитанных показателей"
    )
    frame: str = Field(..., description="Ссылка на обработанный кадр")