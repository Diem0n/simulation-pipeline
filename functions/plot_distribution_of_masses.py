#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 11:52:08 2024

@author: sohaib
"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from .decode_history import decode_history
import config

def plot_distribution_of_masses(x_column, y_column):
    
    data = config.data
    k_values = config.k_values
    
    if x_column not in data.columns or y_column not in data.columns:
        print(f"Error: Columns '{x_column}' or '{y_column}' not found in data.")
        return

    # Print available stellar types (k values)
    print("\nAvailable star types (based on k values):")
    for k, v in k_values.items():
        print(f"{k}: {v}")

    # Prompt for stellar types to include
    selected_ks = input("Enter the k values to include (comma-separated) or press Enter to include all: ").strip()
    
    if selected_ks:
       selected_ks = [int(k.strip()) for k in selected_ks.split(',')]
    
    # Handling the case where either ik1 or ik2 is zero
       filtered_data = data[
        ((data['ik1'].isin(selected_ks)) & (data['ik1'] != 0)) | 
        ((data['ik2'].isin(selected_ks)) & (data['ik2'] != 0))
    ]

    # For rows where ik1 or ik2 is 0, check the ikb value and mass columns
       if 0 in selected_ks:
               ikb_zero_mask = data['ikb'] == 0
        
        # Identify where ik1 is 0 and sm1 is 0 (then set ik1 to NaN)
               ik1_zero_mask = (data['ik1'] == 0) & ~ikb_zero_mask & (data['sm1'] == 0)
               data.loc[ik1_zero_mask, 'ik1'] = np.nan

        # Identify where ik2 is 0 and sm2 is 0 (then set ik2 to NaN)
               ik2_zero_mask = (data['ik2'] == 0) & ~ikb_zero_mask & (data['sm2'] == 0)
               data.loc[ik2_zero_mask, 'ik2'] = np.nan

        # Create a mask for rows where either ik1 or ik2 was set to NaN
               zero_inclusion_mask = ik1_zero_mask | ik2_zero_mask

        # Append the rows where ik1 or ik2 is zero and mass is zero (now NaN)
               filtered_data = pd.concat([filtered_data, data[zero_inclusion_mask]])

    else:
            filtered_data = data.copy()
     
    # Prompt for mass range filter
    mass_min_input = input("Enter the minimum mass (optional): ").strip()
    mass_max_input = input("Enter the maximum mass (optional): ").strip()
    
    mass_min = float(mass_min_input) if mass_min_input else filtered_data[['sm1', 'sm2']].min().min()
    mass_max = float(mass_max_input) if mass_max_input else filtered_data[['sm1', 'sm2']].max().max()
    filtered_data = filtered_data[((filtered_data['sm1'] >= mass_min) & (filtered_data['sm1'] <= mass_max)) | 
                                  ((filtered_data['sm2'] >= mass_min) & (filtered_data['sm2'] <= mass_max))]

    # Prompt for radial position filter
    r_min_input = input("Enter the minimum radial position (optional): ").strip()
    r_max_input = input("Enter the maximum radial position (optional): ").strip()
    
    r_min = float(r_min_input) if r_min_input else filtered_data['r'].min()
    r_max = float(r_max_input) if r_max_input else filtered_data['r'].max()
    filtered_data = filtered_data[(filtered_data['r'] >= r_min) & (filtered_data['r'] <= r_max)]
    
    # Total count of filtered data
    total_count = len(filtered_data)

    # Count of each stellar type
    star_type_counts = filtered_data['star_type'].value_counts()

    filtered_data.reset_index(drop=True, inplace=True)
    
    # Getting the unique star types to maintain consistent order
    star_type_order = filtered_data['star_type'].unique()

    # List of filled markers 
    filled_markers = ['o', 's', 'D', 'v', '^', '<', '>', 'P', '*', 'X', 'h', 'H', 'd']  
    num_needed_markers = len(star_type_order)
    
    # Repeat markers if needed to ensure there are enough
    if num_needed_markers > len(filled_markers):
        extended_markers = (filled_markers * (num_needed_markers // len(filled_markers) + 1))[:num_needed_markers]
    else:
        extended_markers = filled_markers[:num_needed_markers]

    # Custom style dictionary
    custom_style = {star_type: marker for star_type, marker in zip(star_type_order, extended_markers)}

    # Custom palette for the plot
    palette = sns.color_palette("viridis", len(star_type_order))
    custom_palette = {star_type: color for star_type, color in zip(star_type_order, palette)}

    # Scatter plot
    plt.figure(figsize=(12, 8))
    
    scatter_plot = sns.scatterplot(
        x=filtered_data[x_column], 
        y=filtered_data[y_column], 
        hue=filtered_data['star_type'], 
        style=filtered_data['star_type'],  # Used star_type for style
        palette=custom_palette, 
        markers=custom_style,  
        alpha=0.7,
        hue_order=star_type_order,  # Ensuring hue_order aligns with style_order
        style_order=star_type_order
    )
    
    # Click event handler function
    def on_click(event):
        if event.inaxes != scatter_plot.axes:
            return
        
        # Nearest data point to the mouse cursor 
        distances = np.sqrt((filtered_data[x_column] - event.xdata) ** 2 + (filtered_data[y_column] - event.ydata) ** 2)
        nearest_idx = distances.idxmin()
        nearest_row = filtered_data.iloc[nearest_idx]  

        # Print details
        print(f"\nObject ID: {nearest_row['im']}")
        print(f"System Components: {nearest_row['star_type']}")
        print(f"ID1: {nearest_row['idd1']}, ID2: {nearest_row['idd2']}")
        print(f"Mass of first component: {nearest_row['sm1']} M_sun, Mass of second component: {nearest_row['sm2']} M_sun")
        print(f"Eccentricity: {nearest_row['e']}")
        print(f"Semi-Major Axis: {nearest_row['a']} Rsun")
        
        if abs(nearest_row['idd1'] - nearest_row['idd2']) == 1:
            print("This object is a primordial binary.")
        
        # Decoding and displaying hist1 and hist2 in a DataFrame
        hist1_decoded = decode_history(nearest_row['hist1'])
        hist2_decoded = decode_history(nearest_row['hist2'])
        
        if not hist1_decoded and not hist2_decoded:
            print("No significant history events recorded.")
        else:
            df = pd.DataFrame({
                'History 1': hist1_decoded + [''] * (len(hist2_decoded) - len(hist1_decoded)),
                'History 2': hist2_decoded + [''] * (len(hist1_decoded) - len(hist2_decoded))
            })
            print("\nHistory of Events:")
            print(df.to_string(index=False))
    
    # Connecting the click event
    plt.gcf().canvas.mpl_connect('button_press_event', on_click)
    
    # Adjusting legend to include counts
    plt.legend(
        loc='upper left', 
        bbox_to_anchor=(1, 1), 
        title='Star Type', 
        title_fontsize='13', 
        fontsize='11',
        labels=[f'{star_type} ({star_type_counts[star_type]})' for star_type in star_type_order],
        handles=scatter_plot.legend_.legendHandles  # Use the correct legend handles
    )
    
    # Adding the mass, radial pos range, and total count information
    plt.text(
        0.05, 0.95, 
        f"Mass range: {mass_min:.2f} - {mass_max:.2f} M_sun\nRadial position range: {r_min:.2f} - {r_max:.2f} pc\nTotal count: {total_count}",
        transform=plt.gca().transAxes, 
        fontsize=10, 
        verticalalignment='top', 
        horizontalalignment='left',
        bbox=dict(boxstyle="round,pad=0.3", edgecolor="black", facecolor="lightgray")
    )

    plt.title(f'Distribution of Masses: {x_column} vs {y_column}')
    plt.xlabel(x_column)
    plt.ylabel(y_column)
    plt.grid(True)
    plt.tight_layout(rect=[0, 0, 0.8, 1])  # You can adjust this layout to make room for the legend
    plt.show(block=False)
    plt.pause(0.1)  # Allow the plot to display
    
    # Prompt user if they want to save the filtered data
    save_data_prompt = input("Would you like to save the filtered data to a CSV file? (y/n): ").strip().lower()
    if save_data_prompt == 'y':
        file_name = input("Enter the file name (without extension): ").strip() + '.csv'
        filtered_data.to_csv(file_name, index=False)
        print(f"Filtered data saved as {file_name}.")
    else:
        print("Data not saved.")