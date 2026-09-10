import logging
import pandas as pd
from pathlib import Path
from src.hr_optimizer import optimize_staffing

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)

def generate_roi_aggregation():
    logger.info("Loading historical data from Master.xlsx...")
    df = pd.read_excel('data/Master.xlsx')
    
    # Filter historical dataset (2019-2025) and drop missing occupancy records
    df = df[df['Year'] >= 2019].dropna(subset=['Occupied_Rooms']).copy()
    
    results = []
    
    logger.info("Simulating AI staffing recommendations for historical data...")
    for _, row in df.iterrows():
        hotel_id = row['Hotel_ID']
        date_str = str(row['Date'].date())
        occupied_rooms = int(row['Occupied_Rooms'])
        
        ai_rec = optimize_staffing(hotel_id, date_str, occupied_rooms)
        
        results.append({
            'Date': row['Date'],
            'Year': row['Year'],
            'Month': row['Month'],
            'Hotel_ID': hotel_id,
            'Actual_Housekeeping': row['Total_Household_Employees'],
            'Actual_Kitchen': row['Total_Kitchen_Employees'],
            'Actual_Waiters': row['Total_Waiters_Employees'],
            'AI_Housekeeping': ai_rec['Housekeeping'],
            'AI_Kitchen': ai_rec['Kitchen'],
            'AI_Waiters': ai_rec['Waiters']
        })
        
    df_results = pd.DataFrame(results)
    
    logger.info("Aggregating data by Year and Month...")
    grouped = df_results.groupby(['Year', 'Month', 'Hotel_ID']).sum(numeric_only=True).reset_index()
    
    # Calculate operational totals and savings
    grouped['Actual_Total'] = grouped['Actual_Housekeeping'] + grouped['Actual_Kitchen'] + grouped['Actual_Waiters']
    grouped['AI_Total'] = grouped['AI_Housekeeping'] + grouped['AI_Kitchen'] + grouped['AI_Waiters']
    
    grouped['Saved_Shifts'] = grouped['Actual_Total'] - grouped['AI_Total']
    grouped['Saved_Shifts'] = grouped['Saved_Shifts'].clip(lower=0) 
    grouped['Saved_Hours'] = grouped['Saved_Shifts'] * 7
    
    output_path = Path('outputs/roi_monthly_agg.csv')
    output_path.parent.mkdir(exist_ok=True)
    grouped.to_csv(output_path, index=False)
    
    logger.info(f"ROI aggregation successfully exported to {output_path}")

if __name__ == "__main__":
    generate_roi_aggregation()