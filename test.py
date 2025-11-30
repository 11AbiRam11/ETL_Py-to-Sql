year_months = list()
for year in range(2000, 2025):
    for month in range(1, 13):
        year_months.append(f"{year}-{month:02d}")
        print(f"{year}-{month:02d}")
print(len(year_months))
