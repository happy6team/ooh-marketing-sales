from loaders.brand_loader import load_brand
# from loaders.sales_status_loader import load_sales_status
# from loaders.campaign_status_loader import load_campaign_status
from loaders.media_loader import load_media
from loaders.campaign_loader import load_campaign
from loaders.campaign_media_loader import load_campaign_media
from loaders.sales_log_loader import load_sales_log

async def load_all_data(session):
    # await load_sales_status("data/sales_status.csv", session)
    await load_brand("data/brand.csv", session)
    # await load_campaign_status("data/campaign_status.csv", session)
    await load_media("data/media.csv", session)
    await load_campaign("data/campaign.csv", session)
    await load_campaign_media("data/campaign_media.csv", session)
    await load_sales_log("data/sales_log.csv", session)
