from random_forest import RandomForestSignalClassifier
clf = RandomForestSignalClassifier()
clf.load_model("main_rf.pkl")


def get_easy_signal(df, i):
    if i < 2:
        return "NEUTRAL"
    row = df.iloc[i]
    return clf.predict(row)
