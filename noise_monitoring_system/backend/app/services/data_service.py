"""
噪声数据服务 (含导入引擎)
"""
import csv
import io
from datetime import datetime
from decimal import Decimal
from typing import BinaryIO, List, Optional

from sqlalchemy.orm import Session

from app.models import NoiseReading, IngestionJob
from app.repositories import NoiseReadingRepository, IngestionJobRepository
from app.schemas import NoiseReadingCreate


class NoiseDataService:
    """噪声数据服务 (含导入引擎)"""

    @staticmethod
    def add_reading(db: Session, data: NoiseReadingCreate) -> NoiseReading:
        """添加单条噪声数据"""
        reading = NoiseReading(
            point_id=data.point_id,
            device_id=data.device_id,
            measured_at=data.measured_at,
            db_value=data.db_value,
            temperature=data.temperature,
            humidity=data.humidity
        )
        return NoiseReadingRepository.create(db, reading)

    @staticmethod
    def bulk_add_readings(db: Session, readings_data: List[NoiseReadingCreate]) -> int:
        """批量添加噪声数据"""
        readings = [
            NoiseReading(
                point_id=data.point_id,
                device_id=data.device_id,
                measured_at=data.measured_at,
                db_value=data.db_value,
                temperature=data.temperature,
                humidity=data.humidity
            )
            for data in readings_data
        ]
        return NoiseReadingRepository.bulk_create(db, readings)

    @staticmethod
    def import_from_csv(
        db: Session, 
        file_content: BinaryIO, 
        source: str = "csv_upload"
    ) -> IngestionJob:
        """
        CSV 数据导入引擎
        支持两种格式:
        1. 标准格式: point_id, measured_at, db_value, temperature, humidity
        2. 大鹏新区格式: 站点编码, 站点名称, 监测时间, 等效声级dB
        """
        job = IngestionJob(
            source=source, 
            status="running", 
            started_at=datetime.utcnow()
        )
        IngestionJobRepository.create(db, job)

        try:
            # 尝试不同编码读取文件
            raw_content = file_content.read()
            content = None
            for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
                try:
                    content = raw_content.decode(encoding)
                    print(f"[CSV导入] 使用编码: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise ValueError("无法解码CSV文件，请检查文件编码")
            
            reader = csv.DictReader(io.StringIO(content))
            readings = []
            
            # 检测CSV格式
            fieldnames = reader.fieldnames or []
            print(f"[CSV导入] 检测到列名: {fieldnames}")
            is_dapeng_format = '站点编码' in fieldnames and '等效声级dB' in fieldnames
            print(f"[CSV导入] 是否大鹏格式: {is_dapeng_format}")

            for row in reader:
                try:
                    if is_dapeng_format:
                        # 大鹏新区格式
                        point_id = int(row["站点编码"])
                        # 解析时间格式: 2025/1/15 14:00 或 2025-01-15 14:00:00
                        time_str = row["监测时间"]
                        try:
                            measured_at = datetime.strptime(time_str, "%Y/%m/%d %H:%M")
                        except ValueError:
                            try:
                                measured_at = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                measured_at = datetime.fromisoformat(time_str)
                        db_value = Decimal(row["等效声级dB"])
                        temperature = None
                        humidity = None
                    else:
                        # 标准格式
                        point_id = int(row["point_id"])
                        measured_at = datetime.fromisoformat(row["measured_at"])
                        db_value = Decimal(row["db_value"])
                        temperature = Decimal(row["temperature"]) if row.get("temperature") else None
                        humidity = Decimal(row["humidity"]) if row.get("humidity") else None
                    
                    reading = NoiseReading(
                        point_id=point_id,
                        measured_at=measured_at,
                        db_value=db_value,
                        temperature=temperature,
                        humidity=humidity
                    )
                    readings.append(reading)
                except (KeyError, ValueError) as e:
                    # 跳过无效行
                    print(f"[CSV导入] 跳过无效行: {row}, 错误: {e}")
                    continue

            print(f"[CSV导入] 解析完成，共 {len(readings)} 条记录准备写入")
            count = NoiseReadingRepository.bulk_create(db, readings)
            print(f"[CSV导入] 写入完成，成功 {count} 条")
            job.status = "success"
            job.records_count = count
        except Exception as e:
            job.status = "failed"
            job.records_count = 0
            # 记录错误但不重新抛出，让任务记录下来
            import traceback
            print(f"CSV导入失败: {str(e)}")
            traceback.print_exc()
        finally:
            job.finished_at = datetime.utcnow()
            IngestionJobRepository.update(db, job)

        return job

    @staticmethod
    def get_point_history(
        db: Session, 
        point_id: int, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[NoiseReading]:
        """获取监测点历史数据"""
        return NoiseReadingRepository.get_by_point_and_time(
            db, point_id, start_time, end_time
        )

    @staticmethod
    def get_hourly_trend(
        db: Session, 
        start_time: datetime, 
        end_time: datetime, 
        point_id: Optional[int] = None
    ) -> List[dict]:
        """获取小时趋势数据"""
        return NoiseReadingRepository.get_hourly_trend(
            db, start_time, end_time, point_id
        )

    @staticmethod
    def get_time_bucket_data(
        db: Session, 
        start_time: datetime, 
        end_time: datetime, 
        interval: str = "1 hour"
    ) -> List[dict]:
        """获取时间桶聚合数据（用于时间轴回溯）"""
        return NoiseReadingRepository.get_time_bucket_data(
            db, start_time, end_time, interval
        )

    @staticmethod
    def get_daily_stats(
        db: Session,
        start_time: datetime,
        end_time: datetime,
        area_id: Optional[int] = None
    ) -> List[dict]:
        """获取每日统计数据"""
        return NoiseReadingRepository.get_daily_stats(
            db, start_time, end_time, area_id
        )

    @staticmethod
    def get_today_avg(db: Session) -> Decimal:
        """获取今日平均噪声"""
        return NoiseReadingRepository.get_today_avg(db)

    @staticmethod
    def get_today_count(db: Session) -> int:
        """获取今日采样数"""
        return NoiseReadingRepository.get_today_count(db)

    @staticmethod
    def get_exceed_rate(
        db: Session, 
        start_time: datetime, 
        end_time: datetime
    ) -> Decimal:
        """计算超标率"""
        return NoiseReadingRepository.get_exceed_rate(db, start_time, end_time)

    @staticmethod
    def get_ingestion_jobs(db: Session, skip: int = 0, limit: int = 100) -> List[IngestionJob]:
        """获取数据导入任务列表"""
        return IngestionJobRepository.get_all(db, skip, limit)
