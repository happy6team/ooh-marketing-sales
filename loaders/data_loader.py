from loaders.brand_loader import load_brand
from loaders.media_loader import load_media
from loaders.campaign_loader import load_campaign
from loaders.campaign_media_loader import load_campaign_media
from loaders.sales_log_loader import load_sales_log
from loaders.media_match_loader import load_brand_media_match

async def load_all_data(session):
    await load_brand("data/data_sample/brand.csv", session)
    await load_media("data/data_sample/media.csv", session)
    await load_campaign("data/data_sample/campaign.csv", session)
    await load_campaign_media("data/data_sample/campaign_media.csv", session)
    await load_sales_log("data/data_sample/sales_log.csv", session)
    await load_brand_media_match("data/data_sample/media_match.csv", session)
