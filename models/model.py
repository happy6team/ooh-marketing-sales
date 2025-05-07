from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Date, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import declarative_base

Base = declarative_base(cls=AsyncAttrs)

# SalesStatus 테이블
class SalesStatus(Base):
    __tablename__ = "sales_statuses"

    sales_status_id = Column(Integer, primary_key=True, index=True)
    status_name = Column(String(50), nullable=False)
    description = Column(Text)
    sort_order = Column(Integer)
    is_final = Column(Boolean, default=False)

    # SalesLog와의 관계 설정 (1:N 관계)
    sales_logs = relationship("SalesLog", back_populates="sales_status")

    # Brand와의 관계 설정 (1:N 관계)
    brands = relationship("Brand", back_populates="sales_status")

# Brand 테이블
class Brand(Base):
    __tablename__ = "brands"

    brand_id = Column(Integer, primary_key=True, index=True)
    subsidiary_id = Column(Integer)
    brand_name = Column(String(255), nullable=False)
    main_phone_number = Column(String(50))
    manager_email = Column(String(255))
    manager_phone_number = Column(String(50))
    sales_status_id = Column(Integer, ForeignKey("sales_statuses.sales_status_id"))
    sales_status_note = Column(String(255))

    # SalesStatus와의 관계 설정 (1:N 관계)
    sales_status = relationship("SalesStatus", back_populates="brands")

    # SalesLog와의 관계 설정 (1:N 관계)
    sales_logs = relationship("SalesLog", back_populates="brand")
    
    # Brand와 Campaign은 1:N 관계 추가
    campaigns = relationship("Campaign", back_populates="brand")

# Campaign 테이블
class Campaign(Base):
    __tablename__ = "campaigns"

    campaign_id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.brand_id"), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    status_id = Column(Integer, ForeignKey("campaign_statuses.campaign_status_id"))
    total_budget = Column(Float)

    # 관계 설정: Campaign과 CampaignMedia는 1:N 관계
    campaign_medias = relationship("CampaignMedia", back_populates="campaign")

    # Campaign과 Brand는 N:1 관계
    brand = relationship("Brand", back_populates="campaigns")
    
    # Campaign과 CampaignStatus는 N:1 관계
    status = relationship("CampaignStatus", back_populates="campaigns")

# CampaignStatus 테이블
class CampaignStatus(Base):
    __tablename__ = "campaign_statuses"

    campaign_status_id = Column(Integer, primary_key=True, index=True)
    status_name = Column(String(100), nullable=False)

    # 관계 설정: CampaignStatus와 Campaign은 1:N 관계
    campaigns = relationship("Campaign", back_populates="status")
    
    # 관계 설정: CampaignStatus와 CampaignMedia는 1:N 관계
    campaign_medias = relationship("CampaignMedia", back_populates="status")

# Media 테이블
class Media(Base):
    __tablename__ = "medias"

    media_id = Column(Integer, primary_key=True, index=True)
    media_name = Column(String(255), nullable=False)
    location = Column(String(255))
    specification = Column(String(100))
    slot_count = Column(Integer)
    media_type = Column(String(100))
    operating_hours = Column(String(50))
    guaranteed_exposure = Column(Integer)
    duration_seconds = Column(Integer)
    quantity = Column(Integer)
    unit_price = Column(Float)
    features = Column(Text)
    image_day_url = Column(String(255))
    image_night_url = Column(String(255))
    image_map_url = Column(String(255))

    # 관계 설정: Media와 CampaignMedia는 1:N 관계
    campaign_medias = relationship("CampaignMedia", back_populates="media")

class CampaignMedia(Base):
    __tablename__ = "campaign_medias"

    campaign_media_id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.campaign_id"), nullable=False)
    media_id = Column(Integer, ForeignKey("medias.media_id"), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    slot_count = Column(Integer)
    executed_price = Column(Float)
    execution_image_url = Column(String(255))
    campaign_status_id = Column(Integer, ForeignKey("campaign_statuses.campaign_status_id"), nullable=False)

    # 관계 설정: CampaignMedia와 Campaign은 N:1 관계
    campaign = relationship("Campaign", back_populates="campaign_medias", single_parent=True)

    # CampaignMedia와 CampaignStatus는 N:1 관계
    status = relationship("CampaignStatus", back_populates="campaign_medias")

    # CampaignMedia와 Media는 N:1 관계
    media = relationship("Media", back_populates="campaign_medias")


# SalesLog 테이블
class SalesLog(Base):
    __tablename__ = "sales_logs"

    sales_log_id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.brand_id"))
    brand_name = Column(String(255), nullable=False)
    manager_name = Column(String(255), nullable=False)
    manager_email = Column(String(255))
    agent_name = Column(String(255))
    contact_time = Column(DateTime)
    contact_method = Column(String(50))
    call_memo = Column(Text)
    client_needs_summary = Column(Text)
    followup_date = Column(Date)
    sales_status_id = Column(Integer, ForeignKey("sales_statuses.sales_status_id"))
    proposal_uri = Column(String(255))
    is_proposal_generated = Column(Boolean, default=False)
    last_updated_at = Column(DateTime)
    remarks = Column(Text)

    # Brand와의 관계 설정 (N:1 관계)
    brand = relationship("Brand", back_populates="sales_logs")

    # SalesStatus와의 관계 설정 (N:1 관계)
    sales_status = relationship("SalesStatus", back_populates="sales_logs")
