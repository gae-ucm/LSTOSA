import datetime
import glob
import operator
import os
import os.path
import sys

iflag = None
daqdir = None


def Usage():
    message = f"Usage: {sys.argv[0]} [-i] <raw_dir>\n"
    message += "where:\n"
    message += "  raw_dir   directory containing the raw files to be processed\n"
    message += "  -i        incomplete data, do not consider the last run"
    return message


def Format_date(d):
    sep = "-"
    return d.strftime("%Y" + sep + "%m" + sep + "%d")


def Format_time(t):
    sep = ":"
    return t.strftime("%H" + sep + "%M" + sep + "%S")


def read_args():
    global iflag
    global daqdir
    try:
        assert len(sys.argv[1:]) == 1 or len(sys.argv[1:]) == 2
        if len(sys.argv[1:]) == 1:
            iflag = False
        elif len(sys.argv[1:]) == 2:
            assert sys.argv[1] == "-i"
            # drop the first value (-i) to get the previous case
            sys.argv.remove(sys.argv[1])
            iflag = True
    except:
        # input arguments seem wrong
        print(Usage())
        sys.stderr.write(f"ERROR [{sys.argv[0]}]: Wrong arguments ({', '.join(sys.argv[1:])})\n")
        sys.stderr.flush()
        sys.exit(1)

    try:
        assert os.path.isdir(sys.argv[1])
        assert glob.glob(sys.argv[1] + "/2*.raw*") != []
    except:
        daqdir = 0
        try:
            telescope = sys.argv[1].split("/")[2]
            date_array = sys.argv[1].split("/")[-1].split("_")
            existing_nightsummary = (
                "/data/"
                + telescope
                + "/OSA/Analysis/"
                + "/".join(date_array)
                + "/NightSummary_"
                + "".join(date_array)
                + "_"
                + telescope
                + ".txt"
            )
            os.path.isfile(existing_nightsummary)
        except:
            # cannot generate nightsummary
            print(Usage())
            sys.stderr.write(f"ERROR [{sys.argv[0]}]: Cannot find Nightsummary / RAW_dir. ({', '.join(sys.argv[1:])})\n")
            sys.stderr.flush()
            sys.exit(1)
    else:
        daqdir = sys.argv[1]


class Report:
    def __init__(self, filename):
        basename = os.path.basename(filename)
        self.get_run_report(basename)

        # self.search_rep(basename)
        # self.get_drive_report()
        # self.get_cc_report()

    def get_run_report(self, basename):
        # dir template
        rep_path = "/data/_TEL_/OSA/CC/_DATETIME_/"

        # fill telescope
        if "LST1" in basename:
            TEL = "LST1"
        elif "LST2" in basename:
            TEL = "LST2"

        rep_path = rep_path.replace("_TEL_", TEL)

        # fill datetime
        rep_path = rep_path.replace("_DATETIME_", basename[0:4] + "_" + basename[4:6] + "_" + basename[6:8])

        # run report content
        self.run_rep_content = []
        for fpath in glob.glob(rep_path + "/CC*" + TEL + "*.run"):
            with open(fpath) as fopen:
                self.run_rep_content.extend(fopen.readlines())

    def default_values(self):
        self.zd = -1
        self.az = -1
        self.events = -1
        self.L2Table = -1
        self.L2Rate = -1
        self.HV_set = -1
        self.mjd = -1
        self.ra = -1
        self.dec = -1
        self.test = "No_Test"
        self.moon = "No_Moon"
        self.filters = "No_Filter"
        self.RedHV = False

    def analyze_run_report(self, run, subrun, rtype):
        try:
            # start from default values
            self.default_values()

            # extract the line that matches the run.subrun criteria
            # (keep the last one if there are multiple choices)
            # print(" ".join([run.lstrip("0"),subrun.lstrip("0"),rtype]))
            check = " ".join([run.lstrip("0"), subrun.lstrip("0"), rtype])
            selected_line = [ln.strip("\n") for ln in self.run_rep_content if check in ln][-1].split(" ")

            self.zd = selected_line[9]
            self.az = selected_line[10]
            self.events = selected_line[11]
            self.L2Table = selected_line[14]
            self.L2Rate = selected_line[17]
            self.HV_set = selected_line[20]
            self.mjd = selected_line[37]
            self.ra = selected_line[42]
            self.dec = selected_line[43]
            self.test = selected_line[38]
            self.moon = selected_line[39]
            self.filters = selected_line[62]

            #### FIXME. THIS IS A CHAPUZA !!!!: REMOVE n/a when the missing flatfielding issue is addressed
            # known_redHV = [\
            #  'n/a',\
            #  'HV_LST1_flatfielding_4kQ_20131114',\
            #  'HV_LST2_flatfielding_3750Q_20131114']
            known_redHV = [
                "HV_LST1_flatfielding_4kQ_20131114",
                "HV_LST2_flatfielding_3750Q_20131114",
                "HV_LST1_flatfielding_reduced_20151112",
                "HV_LST2_flatfielding_reduced_20151112",
                "HV_LST1_flatfielding_reduced_20160709",
            ]
            if self.HV_set in known_redHV or "_reduced_" in self.HV_set:
                self.RedHV = True
        except:
            # sys.stderr.write(\
            #   "WARNING [%s]: Cannot parse .run reports. "+\
            #   "Using default values \n")

            sys.stderr.flush()
            self.default_values()

            # try with the previous subrun
            if int(subrun) > 1:
                self.analyze_run_report(run, str(int(subrun) - 1), rtype)
            # raise

    def search_rep(self, basename):
        # dir template
        rep_path = "/data/_TEL_/OSA/CC/_DATETIME_/"

        # fill telescope
        if "LST1" in basename:
            rep_path = rep_path.replace("_TEL_", "LST1")
        elif "LST2" in basename:
            rep_path = rep_path.replace("_TEL_", "LST2")

        # fill datetime
        rep_path = rep_path.replace("_DATETIME_", basename[0:4] + "_" + basename[4:6] + "_" + basename[6:8])

        self.rep_file = rep_path + basename.split(".raw")[0] + ".rep"
        if os.path.isfile(self.rep_file):
            self.is_available = True
            with open(self.rep_file) as f:
                self.rep_content = f.readlines()
        else:
            self.is_available = False

    ##########
    # OLD CODE
    def get_drive_report(self):
        try:
            assert self.is_available == True
            # load the first drive entry
            drive_entry = [ln for ln in self.rep_content if "DRIVE-REPORT" in ln][0].split(" ")
        except:
            # default values
            self.ra = -1
            self.dec = -1
            self.tcul = -1
            self.mjd = -1
            self.zd = -1
        else:
            # extract values
            self.ra = drive_entry[18] + drive_entry[19] + ":" + drive_entry[20] + ":" + drive_entry[21][1:]
            self.dec = drive_entry[22] + drive_entry[23] + ":" + drive_entry[24] + ":" + drive_entry[25][1:]
            self.tcul = drive_entry[26] + drive_entry[27] + ":" + drive_entry[28] + ":" + drive_entry[29][1:]
            self.mjd = float(drive_entry[30])
            self.zd = drive_entry[31] + drive_entry[32] + ":" + drive_entry[33] + ":" + drive_entry[33][1:]

    def get_cc_report(self):
        try:
            assert self.is_available == True
            # load the first drive entry
            cc_entry = [ln for ln in self.rep_content if "CC-REPORT" in ln][0].split(" ")
        except:
            # default values
            self.grb = 0
            self.moon = "No_Moon"
        else:
            # extract values
            self.moon = cc_entry[60]
            self.grb = cc_entry[62]


def main():

    if daqdir == 0:
        telescope = sys.argv[1].split("/")[2]
        date_array = sys.argv[1].split("/")[-1].split("_")
        existing_nightsummary = (
            "/data/"
            + telescope
            + "/OSA/Analysis/"
            + "/".join(date_array)
            + "/NightSummary_"
            + "".join(date_array)
            + "_"
            + telescope
            + ".txt"
        )
        print(open(existing_nightsummary).read().strip())
        sys.exit(0)

    suffix = [".raw", ".raw.gz"]
    files = []
    for s in suffix:
        files.extend(glob.glob(daqdir + "/*" + s))

    # we include a check to know if there were no files
    # or directory was undergoing a gzip operation
    istherearaw = False
    istherearawgz = False

    if len(files) == 0:
        sys.stderr.write(f"ERROR [{sys.argv[0]}]: No files with extension ({', '.join(suffix)}) found in directory {daqdir}\n")
        sys.stderr.flush()
        sys.exit(1)

    else:
        for f in files:
            if ".raw" + ".raw".join(f.split(".raw")[1:]) == suffix[0]:
                istherearaw = True
            if ".raw" + ".raw".join(f.split(".raw")[1:]) == suffix[1]:
                istherearawgz = True

            if istherearaw == True and istherearawgz == True:
                sys.stderr.write(f"ERROR [{sys.argv[0]}]:Files with both extensions ({', '.join(suffix)}) found!\n")
                sys.stderr.flush()
                sys.exit(1)

    summary = []

    fReport = Report(files[0])
    for f in files:
        # some default values
        trash = None
        run_number = None
        subrun_number = None
        run_type = None
        project_name = None

        start_date = "0000-00-00"
        start_time = "00:00:00"
        # number_events = -1
        # zd_deg = -1
        # source_ra = -1
        # source_dec = -1
        # L2_table = -1
        test_run = "No_Test"
        hv_setting = "stdHV"
        moonfilters = "No_Filter"
        # moon_conditions = "No_Moon"

        # fReport = Report(f)

        # first we get the last modification time of the file
        mtime = os.path.getmtime(f)
        dt = datetime.datetime.fromtimestamp(mtime)

        start_date = Format_date(dt)
        start_time = Format_time(dt)

        # now some should perform further manipulation on the file name
        filename_array = os.path.basename(f).split("_")
        trash, trash, run_number, run_type = filename_array[0:4]
        project_name = "_".join(filename_array[4:])

        # file name processing
        project_name = project_name.split(".raw")[0]
        # the run_number includes the subrun in RRRRRRRR.SSS format
        run_number, subrun_number = run_number.split(".")
        # SSS may contain unwanted leading zeroes
        subrun_number = subrun_number.lstrip("0")

        # identify the run_type
        if run_type == "D":
            run_type = "DATA"
        elif run_type == "C":
            run_type = "CALIBRATION"
        elif run_type == "P":
            run_type = "PEDESTAL"
        else:
            run_type = "UNKNOWN"
            test_run = "Test"
            continue

        # load the report
        fReport.analyze_run_report(run_number, subrun_number, run_type)
        zd_deg = fReport.zd
        source_ra = fReport.ra
        source_dec = fReport.dec
        # moon_conditions = fReport.moon
        if fReport.RedHV:
            # moon_conditions = "Moon"
            hv_setting = "redHV"
        if fReport.filters == "Filter":
            moonfilters = "Filter"
            # moon_conditions = "Filter"

        # ignore park runs
        if project_name == "Park":
            continue

        test_run = fReport.test
        L2_table = fReport.L2Table
        number_events = fReport.events

        # create our summary line with the sequence information
        summary_seq = [
            mtime,
            int(run_number),
            int(subrun_number),
            run_type,
            start_date,
            start_time,
            project_name,
            number_events,
            zd_deg,
            source_ra,
            source_dec,
            L2_table,
            test_run,
            hv_setting,
            moonfilters,
        ]

        # append it
        summary.append(summary_seq)
        # print(', '.join(summary_seq))

    # another ugly workaround (2015/07/12 - missing CAL at the beginning of the night)
    # summary.append([\
    #    1, 5044394, 1, "CALIBRATION", "2015-07-12", "02:17:50", "GammaCygni-W0.60+045", \
    #    469, 19.4, "20:22:18", "41:11:05", "DEFAULT", "No_Test", "No_Moon"])

    # sort by modification time
    # sortedsummary = sorted(summary, key=lambda row: row[0])
    # sort by run number
    # sortedsummary = sorted(summary, key=lambda row: row[1])
    # sort by run and subrun number
    sortedsummary = sorted(summary, key=operator.itemgetter(1, 2))

    # integrity check in the sorted summary
    # a) more than 1 line
    # b) $run_type = DATA is preceeded by $run_type = DATA or CALIBRATION
    # c) $subrun_number within the same $run_number are in order

    # check if we have at least 1 runs
    if len(sortedsummary) < 1:
        if iflag is False:
            sys.stderr.write(f"ERROR [{sys.argv[0]}]: Less than 1 run found!, \n")
            sys.stderr.flush()
        sys.exit(1)

    for i in range(1, len(sortedsummary)):
        run_number = sortedsummary[i][1]
        subrun_number = sortedsummary[i][2]
        run_type = sortedsummary[i][3]

        if run_type == "DATA":
            previous_run_number = sortedsummary[i - 1][1]
            previous_subrun_number = sortedsummary[i - 1][2]
            previous_run_type = sortedsummary[i - 1][3]

            # CALIBRATION->DATA,DATA,DATA ... PEDESTAL -!-> DATA
            if previous_run_type not in ["CALIBRATION", "DATA"]:
                msg_part1 = f"WARNING [{sys.argv[0]}]: Previous run.subrun {previous_run_number}.{previous_subrun_number} "
                msg_part2 = f"type {previous_run_type} not expected for "
                msg_part3 = f"current {run_number}.{subrun_number} (expected DATA or CALIBRATION)\n"
                sys.stderr.write(msg_part1 + msg_part2 + msg_part3)
                sys.stderr.flush()

            # run.subrun -> run.subrun+1
            if run_number == previous_run_number:
                if int(subrun_number) != int(previous_subrun_number) + 1:
                    msg_part1 = f"WARNING [{sys.argv[0]}]: Previous run.subrun {previous_run_number}.{previous_subrun_number} "
                    msg_part2 = f"and current {previous_run_number}.{subrun_number} are not in sequential order\n"
                    sys.stderr.write(msg_part1 + msg_part2)
                    sys.stderr.flush()

    # print the list of sorted runs (without the mtime)
    for seq in sortedsummary:
        # if iflag is set, then remove the last sequence from the processing queue
        if iflag is True and seq[1] == sortedsummary[-1][1]:
            continue
        print(" ".join([str(k) for k in seq[1:]]))


if __name__ == "__main__":
    read_args()
    main()