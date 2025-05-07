from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Date, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import declarative_base

Base = declarative_base(cls=AsyncAttrs)

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

    # Brand와 SalesStatus 관계 추가
    sales_status = relationship("SalesStatus", back_populates="brands")

    # Brand와 SalesLog 관계 추가
    sales_logs = relationship("SalesLog", back_populates="brand")

class Campaign(Base):
    __tablename__ = "campaigns"  

    campaign_id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.brand_id"), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)
    status_id = Column(Integer, ForeignKey("campaign_statuses.campaign_status_id"))
    total_budget = Column(Float)

    # 관계 설정 추가: Campaign과 CampaignMedia는 1:N 관계
    medias = relationship("CampaignMedia", back_populates="campaign")

    # Campaign과 Brand는 1:N 관계
    brand = relationship("Brand", back_populates="campaigns")

class CampaignStatus(Base):
    __tablename__ = "campaign_statuses"  

    campaign_status_id = Column(Integer, primary_key=True, index=True)
    status_name = Column(String(100), nullable=False)

    # 관계 설정 추가: CampaignStatus와 CampaignMedia는 1:N 관계
    campaign_medias = relationship("CampaignMedia", back_populates="status")

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

    # 관계 설정 추가: Media와 CampaignMedia는 1:N 관계
    campaign_medias = relationship("CampaignMedia", back_populates="media")

class CampaignMedia(Base):
    __tablename__ = "campaign_medias"  

    campaign_media_id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.campaign_id"))
    media_id = Column(Integer, ForeignKey("medias.media_id"))
    start_date = Column(Date)
    end_date = Column(Date)
    slot_count = Column(Integer)
    executed_price = Column(Float)
    execution_image_url = Column(String(255))
    campaign_status_id = Column(Integer, ForeignKey("campaign_statuses.campaign_status_id"))

    # 관계 설정 추가: CampaignMedia와 Campaign은 N:1 관계
    campaign = relationship("Campaign", back_populates="medias")

    # CampaignMedia와 CampaignStatus는 N:1 관계
    status = relationship("CampaignStatus", back_populates="campaign_medias")

    # CampaignMedia와 Media는 N:1 관계
    media = relationship("Media", back_populates="campaign_medias")

class SalesLog(Base):
    __tablename__ = "sales_logs"  # 테이블 이름 수정

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
    sales_status_id = Column(Integer, ForeignKey("sales_statuses.sales_status_id"))  # 수정된 부분
    proposal_uri = Column(String(255))
    is_proposal_generated = Column(Boolean, default=False)
    last_updated_at = Column(DateTime)
    remarks = Column(Text)

    # 관계 설정 추가: SalesLog와 SalesStatus는 N:1 관계
    sales_status = relationship("SalesStatus", back_populates="sales_logs")

    # SalesLog와 Brand는 N:1 관계
    brand = relationship("Brand", back_populates="sales_logs")

class SalesStatus(Base):
    __tablename__ = "sales_statuses"  

    sales_status_id = Column(Integer, primary_key=True, index=True)
    status_name = Column(String(50), nullable=False)
    description = Column(Text)
    sort_order = Column(Integer)
    is_final = Column(Boolean, default=False)

    # 관계 설정 추가: SalesStatus와 SalesLog는 1:N 관계
    sales_logs = relationship("SalesLog", back_populates="sales_status")
