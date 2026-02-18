from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
import datetime

try:
    from database import Base
except ImportError:
    from ..database import Base

class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, index=True) # Folder name, e.g., "scan_20240101_120000"
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    scanned_by = Column(String, default="Unknown")
    status = Column(String, default="pass") # 'pass', 'fail', 'in_progress'
    batch_folder = Column(String)
    defect_count = Column(Integer, default=0)
    image_count = Column(Integer, default=0)
    
    images = relationship("ScanImage", back_populates="scan", cascade="all, delete-orphan")

class ScanImage(Base):
    __tablename__ = "scan_images"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, ForeignKey("scans.id"), index=True)
    filename = Column(String)
    filepath = Column(String)
    
    # Inference Results
    inference_time_ms = Column(Float, default=0.0)
    defect_count = Column(Integer, default=0)
    has_defects = Column(Boolean, default=False)
    overlay_path = Column(String, nullable=True)
    
    # Metadata as JSON string if needed, or specific columns? 
    # For now, keeping it simple.
    
    scan = relationship("Scan", back_populates="images")

class ServoHealth(Base):
    __tablename__ = "servo_health"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    # X Axis
    x_health = Column(Float)
    x_current = Column(Float)
    x_load = Column(Float)
    x_torque = Column(Float)
    x_peak = Column(Float)
    
    # Y Axis
    y_health = Column(Float)
    y_current = Column(Float)
    y_load = Column(Float)
    y_torque = Column(Float)
    y_peak = Column(Float)
    
    # Z Axis
    z_health = Column(Float)
    z_current = Column(Float)
    z_load = Column(Float)
    z_torque = Column(Float)
    z_peak = Column(Float)


class ServoDailyStat(Base):
    __tablename__ = "servo_daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.datetime.utcnow, index=True) # Normalized to midnight? Or just use timestamp and filter?
    # Actually plan said: date, axis, metric as primary key components or similar. 
    # Let's use a composite unique constraint or just simple rows.
    # To keep it simple and flexible:
    timestamp = Column(DateTime, default=datetime.datetime.utcnow) # Time of the record (updated when max/min changes)
    
    axis = Column(String) # 'x', 'y', 'z'
    metric = Column(String) # 'current', 'load', 'torque', 'peak'
    
    min_val = Column(Float)
    min_time = Column(DateTime)
    
    max_val = Column(Float)
    max_time = Column(DateTime)

# Create index for fast lookup
# Index('idx_daily_stats', ServoDailyStat.date, ServoDailyStat.axis, ServoDailyStat.metric)
