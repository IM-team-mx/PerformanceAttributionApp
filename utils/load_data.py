debug = False


def load_data(col1, col2):
    classif_file = './data/equities_classifications.csv'
    if debug:
        ptf_file = './data/portfolios.csv'
        bm_file = './data/benchmarks.csv'
    else:
        ptf_file = col1.file_uploader('portfolios.csv file', help='File produced by the Performance service')
        bm_file = col2.file_uploader('benchmarks.csv file', help='File produced by the Performance service')

    return ptf_file, bm_file, classif_file
