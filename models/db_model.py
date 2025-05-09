from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Date, Float
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import datetime
import re
import uuid
from sqlalchemy.dialects.mysql import CHAR

Base = declarative_base(cls=AsyncAttrs)

class Brand(Base):
    __tablename__ = "brands"

    brand_id = Column(Integer, primary_key=True, index=True)
    subsidiary_id = Column(String(36), default=lambda: str(uuid.uuid4()))
    brand_name = Column(String(255))
    main_phone_number = Column(String(50))
    manager_email = Column(String(255))
    manager_phone_number = Column(String(50))
    sales_status = Column(String(100))  # 문자열로 변경된 상태
    sales_status_note = Column(String(255))
    category = Column(String(100))
    core_product_summary = Column(Text)
    recent_brand_issues = Column(Text)
    last_updated_at = Column(DateTime, default=datetime.now, nullable=True)

    # 관계 설정
    sales_logs = relationship("SalesLog", back_populates="brand")
    campaigns = relationship("Campaign", back_populates="brand")
    media_matches = relationship('BrandMediaMatch', back_populates='brand')

class Campaign(Base):
    __tablename__ = "campaigns"

    campaign_id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.brand_id"), nullable=False)
    campaign_name = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    campaign_status = Column(String(50))  # 문자열 상태로 처리
    total_budget = Column(Float)

    campaign_medias = relationship("CampaignMedia", back_populates="campaign")
    brand = relationship("Brand", back_populates="campaigns")


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
    image_day_url = Column(String(255))
    image_night_url = Column(String(255))
    image_map_url = Column(String(255))

    # 추가된 필드
    population_target = Column(String(255))
    media_characteristics = Column(Text)
    case_examples = Column(Text)

    campaign_medias = relationship("CampaignMedia", back_populates="media")
    brand_matches = relationship('BrandMediaMatch', back_populates='media')


class CampaignMedia(Base):
    __tablename__ = "campaign_medias"

    campaign_media_id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.campaign_id"), nullable=False)
    media_id = Column(Integer, ForeignKey("medias.media_id"), nullable=False)
    campaign_name = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    slot_count = Column(Integer)
    executed_price = Column(Float)
    execution_image_url = Column(String(255))
    campaign_media_status = Column(String(50))

    campaign = relationship("Campaign", back_populates="campaign_medias", single_parent=True)
    media = relationship("Media", back_populates="campaign_medias")

class SalesLog(Base):
    __tablename__ = "sales_logs"

    sales_log_id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.brand_id"))
    brand_name = Column(String(255))  # CSV에 있으므로 유지
    manager_name = Column(String(255))
    manager_email = Column(String(255))
    agent_name = Column(String(255))
    contact_time = Column(DateTime)
    contact_method = Column(String(50))
    call_full_text = Column(Text)  # 새롭게 추가
    call_memo = Column(Text)
    client_needs_summary = Column(Text)
    sales_status = Column(String(50))
    proposal_url = Column(String(255))  # 변경된 필드명
    is_proposal_generated = Column(Boolean, default=False)
    last_updated_at = Column(DateTime)
    remarks = Column(Text)

    brand = relationship("Brand", back_populates="sales_logs")

class BrandMediaMatch(Base):
    __tablename__ = 'brand_media_matches'

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey('brands.brand_id'))
    media_id = Column(Integer, ForeignKey('medias.media_id')) 
    match_reason = Column(Text, nullable=False)
    sales_call_script = Column(Text, nullable=False)
    proposal_email_part_1 = Column(Text, nullable=True)
    proposal_email_part_2 = Column(Text, nullable=True)
    proposal_email_part_3 = Column(Text, nullable=True)
    generated_at = Column(DateTime, nullable=False)
    used_in_sales = Column(Boolean, nullable=False)
    last_updated_at = Column(DateTime, nullable=True)

    # 'brand' 속성 추가: 'brands' 테이블과의 관계 정의
    brand = relationship('Brand', back_populates='media_matches')

    # 'media'와의 관계
    media = relationship('Media', back_populates='brand_matches')