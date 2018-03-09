## Requirements

* Python 3.6+
* matplotlib (I used version 2.0.2)

## Update data

Run the query in `data_query.sql` against the timini.no database and export the result as .csv. Store it in `waffle.csv` in the top-level folder.

## Run

* Top 10: `python3 waffle.py`
* Top 50: `python3 waffle.py -m 50`
* Top 50 and save image: `python3 waffle.py -m 50 -f top50.png`
* Top 1000 and save a huge image with legend disabled and textbox enabled: `python3 waffle.py -m 1000 -f everyone.png -s 60 -nl -t`

This is the full output of `python3 waffle.py -h`

    usage: waffle.py [-h] [-m MAXRANK] [-src SOURCE] [-f FIG] [-s FIGSIZE] [-t]
                     [-nl] [-ng]
    
    optional arguments:
      -h, --help            show this help message and exit
      -m MAXRANK, --maxrank MAXRANK
                            Max rank to include
      -src SOURCE, --source SOURCE
                            Source CSV file
      -f FIG, --fig FIG     Figure filename
      -s FIGSIZE, --figsize FIGSIZE
                            Figure size
      -t, --textboxes       Do textboxes?
      -nl, --no-legend      Skip legend?
      -ng, --no-grid        Skip grid?

Plotting options can be customized by changing the constants at the top of the script.
