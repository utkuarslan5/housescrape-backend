

def scrape_areas(areas, want_tos):
    from funda_scraper import FundaScraper
    def scrape_area(area, want_to):
        scraper = FundaScraper(area=area, want_to=want_to, find_past=False, page_start=1, n_pages=2, days_since=10)   
        return scraper.run(raw_data=False, save=True)
    
    scrape_tasks = []
    for area in areas:
        for want_to in want_tos:
            scrape_tasks.append(scrape_area(area, want_to))
            
    return scrape_tasks

def combine_csvs(data_dir):
    import glob
    import pandas as pd
    
    csv_files = glob.glob(f'{data_dir}/*.csv')

    df_list = []
    for f in csv_files:
        df = pd.read_csv(f)
        df_list.append(df)

    return pd.concat(df_list, ignore_index=True) # TODO: drop extra index column

import pandas as pd
import os

def remove_photo_column_and_resave(directory):
    # Iterate through all files in the directory
    for filename in os.listdir(directory):
        # Check if the file is a CSV
        if filename.endswith('.csv'):
            file_path = os.path.join(directory, filename)

            # Read the CSV file
            df = pd.read_csv(file_path)

            # Check if the 'photo' column exists and remove it
            if 'photo' in df.columns:
                df = df.drop(columns=['photo'])

                # Prepare the new file name with '_wo_photo' suffix
                new_filename = filename.replace('.csv', '_wo_photo.csv')
                new_file_path = os.path.join(directory, new_filename)

                # Save the modified DataFrame back to CSV with the new name
                df.to_csv(new_file_path, index=False)

# Example usage
directory_path = './data/'
remove_photo_column_and_resave(directory_path)


# Example usage
areas = ["amsterdam", "rotterdam", "hague", "utrecht", "eindhoven", "groningen", "maastricht", "leiden", "haarlem", "breda"]
want_tos = ["buy"]

scrape_areas(areas, want_tos)

df = combine_csvs('./data')
df.to_csv('combined_buy.csv')

