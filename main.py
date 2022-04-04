from datetime import datetime
import re

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
# normally when doing EDA I start with the pandas-profiling package since it is a great base to start from
from pandas_profiling import ProfileReport

filename = "U.S. Presidents Birth and Death Information - Sheet1.csv"

data = pd.read_csv(filename)

# input file has a bad row at the end
data = data.drop(axis=0, index=45)


def parse_date(datestring):
    if pd.isna(datestring):
        return datestring
    try:
        return datetime.strptime(datestring, "%b %d, %Y")
    except ValueError as exception:
        if datestring.startswith("June"):
            datestring = datestring.replace("June", "Jun")
        elif datestring.startswith("July"):
            datestring = datestring.replace("July", "Jul")
        else:
            raise exception
        return datetime.strptime(datestring, "%b %d, %Y")


data["birth date parsed"] = data["BIRTH DATE"].apply(parse_date)
data["death date parsed"] = data["DEATH DATE"].apply(parse_date)
# some presidents arent dead yet so lets account for that
data["death date parsed"] = data["death date parsed"].fillna(
    datetime.now().strftime("%Y-%m-%d")
)
data["death date month"] = (
    data["death date parsed"].apply(lambda d: d.month).astype(int)
)
data["birth date month"] = (
    data["birth date parsed"].apply(lambda d: d.month).astype(int)
)
data["year_of_birth"] = data["birth date parsed"].apply(lambda d: d.year).astype(int)

data["lived_days"] = (data["death date parsed"] - data["birth date parsed"]).apply(
    lambda d: d.days
)
data["lived_years"] = data["lived_days"].apply(lambda d: int(d / 365.25))
data["lived_months"] = (
    data["lived_years"] * 12 + data["death date month"] + 12 - data["birth date month"]
)

data = data.drop(
    columns=[
        "death date parsed",
        "death date month",
        "birth date month",
        "birth date parsed",
    ]
)

data = data.sort_values(by="lived_days", ascending=True)
profile = ProfileReport(data)
with open('pandas_profiling_report.html', 'w') as outfile:
    outfile.write(profile.to_html())

bottom10 = data.head(n=10)
top10 = data.tail(n=10).sort_values(by="lived_days", ascending=False)

bottom10.to_csv(
    f'shortest_lived_presidents_as_of_{datetime.now().strftime("%Y-%m-%d")}.csv',
    index=False,
)
top10.to_csv(
    f'longest_lived_presidents_as_of_{datetime.now().strftime("%Y-%m-%d")}.csv',
    index=False,
)

measures = {
    "column_name": "lived_days",
    "date_calculated": datetime.now().strftime("%Y-%m-%d"),
    "mean": data.lived_days.mean(),
    "median": data.lived_days.median(),
    "max": data.lived_days.max(),
    "min": data.lived_days.min(),
    "standard_deviation": data.lived_days.std(),
}

# all the presidents lived different amount of days
measures["mode"] = (
    data.lived_days.mode() if len(data.lived_days.mode()) < len(data) else "N/A"
)
# there are no weights to apply
measures["weighted_mean"] = "N/A"

lived_measures = pd.DataFrame.from_records([measures])
lived_measures.to_csv(
    f'lived_days_measures_as_of_{datetime.now().strftime("%Y-%m-%d")}.csv', index=False
)

report_filename = f'report_generated_{datetime.now().strftime("%Y-%m-%d")}.md'

sns.set_theme(style="whitegrid")
sns.violinplot(x=data[ 'lived_days' ])
plt.savefig('./lived_days_plot.png')
plt.clf()
sns.scatterplot(x=data[ 'year_of_birth' ], y=data['lived_days'])
plt.savefig('./birth_lived_days_scatter.png')

with open(report_filename, "w") as outfile:
    report = f"""# President Age report

    Author: Patrick White
    Date: {datetime.now().strftime("%Y-%m-%d")}

    ## Overview

    Our presidents are getting older. However this cannot be ascribed to just advancing medical science since
    the lived days year of birth correlation is quadratic. JFK is an obvious outlier and should probably be
    removed along with McKinley.

    Further analysis should include the years over which the president served. Anecdotally we see that presidents
    visibly age over the course of their service. The author wonders what the data would show.

    ### Plots

    ![Lived Days](lived_days_plot.png)

    ![Birth Year and Lived Days](birth_lived_days_scatter.png)

    ## Methodology

    ### Cleaning and Preparation

    The original dataset contained a row which did not have information pertinent to a presidents lifespan. This was dropped.
    Many current and former presidents are still alive so a synthetic death date was added on the date that
    this report and analysis was generated. This date is {datetime.now().strftime("%Y-%m-%d")}. If you are reading this
    report after, please adjust the already considerable ages upward or rerun the code `main.py`.

    ### Variables

    The enhanced dataset contains variables called `lived_years` and `lived_months`. These measures are "floored". This
    means that if someone is one day before their 100th birthday on the day this report was run,
    this report would count them as having a `lived_years` of 99.

    ### `lived_days` aggregate measures

    In the appendix there are aggregate measures for the `lived_days` variable. The brief for this report says to include
    a weighted mean but does not provide weights with which one could weight the mean, so it was not calculated. At the
    time of running the report every `lived_days` value was unique so no mode could be calculated.

    ## Appendix

    CSV versions of the following file can be found in the same directory as this report.

    ### Enhanced Data

    {data.to_markdown(index=False)}

    ### Shortest Lived Presidents

    {bottom10.to_markdown(index=False)}

    ### Longest Lived Presidents

    {top10.to_markdown(index=False)}

    ### Lived Days aggregate measures

    {lived_measures.to_markdown(index=False)}

    """
    report = re.sub(r'\n *',r'\n' , report)
    outfile.write(report)
