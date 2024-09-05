import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

# Step 1: Read the data from the file
file_path = 'stress_bilan_1560.txt'
data = pd.read_csv(file_path, delimiter='|', skiprows=1)  # Adjust delimiter and skip the first row

# Step 2: Parse the data to extract T index, T indey, and categories
# Assuming the columns are named 'T_index', 'T_indey', and 'category'
t_index = data[data.columns[1]]
t_indey = data[data.columns[2]]
categories = data[data.columns[3]]

# Step 3: Initialize dictionaries for each category
failed_dict = {}
succeed_dict = {}
# Add more categories if needed

# Step 4: Iterate through the data and populate the dictionaries
for i in range(len(data)):
    t_idx = t_index[i]
    t_idy = t_indey[i]
    category = categories[i]
    
    if t_idx not in failed_dict:
        failed_dict[t_idx] = {}
    failed_dict[t_idx][t_idy] = category

    # Add more conditions for other categories

# Step 5: Convert the dictionaries to DataFrames
failed_df = pd.DataFrame.from_dict(failed_dict, orient='index')
# Add more DataFrames for other categories

# Sort the DataFrames by index and columns and rows
failed_df.sort_index(axis=0, inplace=True)
failed_df.sort_index(axis=1, inplace=True)


# Display the DataFrames
print("Failed Table:")
print(failed_df)

# # Export the DataFrames to CSV
# failed_df.to_csv('stress_bilan_756_output_vector.csv')
# failed_df.to_csv('stress_bilan_1560_failed.csv')

def plot3D(data, title, color):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    # Flatten the DataFrame
    x = np.repeat(data.index, data.shape[1])
    y = np.tile(data.columns, data.shape[0])
    z = data.values.flatten()

    ax.scatter(x, y, z)
    ax.set_title(title)

    # color the points
    ax.scatter(x, y, z, c=color)

    plt.show()

# Example usage
plot3D(failed_df, 'Failed', 'red')
# plot3D(failed_df, 'Succeed', 'yellow')
# plot3D(failed_df, 'Measurement', 'blue')
