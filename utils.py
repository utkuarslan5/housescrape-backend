import asyncio
from funda_scraper import FundaScraper

# # Example usage
# areas = ["amsterdam", "rotterdam", ...] 
# want_tos = ["rent", "buy"]
#
# df = combine_csvs('data')
# df.to_csv('combined.csv')

def scrape_area(area, want_to):
    scraper = FundaScraper(area=area, want_to=want_to, find_past=False, page_start=1, n_pages=50, days_since=30)   
    return scraper.run(raw_data=False, save=True)

async def scrape_areas(areas, want_tos):
    scrape_tasks = []
    for area in areas:
        for want_to in want_tos:
            scrape_tasks.append(scrape_area(area, want_to))
            
    return await asyncio.gather(*scrape_tasks)

def combine_csvs(data_dir):
    import glob
    import pandas as pd
    
    csv_files = glob.glob(f'{data_dir}/*.csv')

    df_list = []
    for f in csv_files:
        df = pd.read_csv(f)
        df_list.append(df)

    return pd.concat(df_list, ignore_index=True)


