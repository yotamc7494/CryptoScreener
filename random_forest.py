import pandas as pd
import numpy as np
import pickle
import os
import pygame
from indicators import add_ll_indicators
from fetcher import load_backtest_data
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.utils.class_weight import compute_sample_weight

CONFIDENCE_THRESHOLD = 0.7


class RandomForestSignalClassifier:
    def __init__(self):
        self.model = HistGradientBoostingClassifier(
            max_iter=1000,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=40,
            learning_rate=0.02,
            max_depth=5,
            l2_regularization=0.0,
            random_state=42
        )
        self.trained = False
        self.classes_ = None
        self.feature_cols = [
            "rsi", "macd", "macd_signal", "macd_hist",
            "stoch_k", "stoch_d",
            "bollinger_band_width", "bollinger_position",
            "volume_change"
        ]

    def prepare_data(self, df):
        # Apply all indicators and drop incomplete rows
        df = add_ll_indicators(df)
        df = df.dropna().copy()

        # Initialize target labels
        df["target"] = "NEUTRAL"
        future_candles = 10
        future_gain = 0.05  # +5% gain triggers BUY
        future_loss = 0.05  # -5% drop triggers SELL

        for i in range(future_candles, len(df) - future_candles):
            curr_close = df.iloc[i]["close"]
            future = df.iloc[i + 1: i + future_candles + 1]

            future_max = future["high"].max()
            future_min = future["low"].min()

            if future_max > curr_close * (1 + future_gain):
                df.at[df.index[i], "target"] = "BUY"
            elif future_min < curr_close * (1 - future_loss):
                df.at[df.index[i], "target"] = "SELL"

        X = df[self.feature_cols]
        y = df["target"]
        return X, y

    def train(self, formatted_data, screen):
        all_X, all_y = [], []
        for symbol, df in formatted_data.items():
            if len(df) <= 5000:
                continue
            df = df.iloc[:-5000]
            X, y = self.prepare_data(df)
            all_X.append(X)
            all_y.append(y)
        if not all_X:
            print("❌ No valid data to train on.")
            return

        X_all = pd.concat(all_X)
        y_all = pd.concat(all_y)

        X_train, X_val, y_train, y_val = train_test_split(X_all, y_all, test_size=0.2, random_state=42)
        class_weights = compute_sample_weight("balanced", y_train)
        self.model.fit(X_train, y_train, sample_weight=class_weights)
        self.trained = True
        self.classes_ = self.model.classes_

        y_probs = self.model.predict_proba(X_val)
        y_probs_train = self.model.predict_proba(X_train)
        
        draw_threshold_graph(screen, y_val, y_probs, self.classes_)
        draw_threshold_graph(screen, y_train, y_probs_train, self.classes_)

    def save_model(self, path="rf_model.pkl"):
        if not self.trained:
            print("❌ Model not trained, nothing to save.")
            return
        with open(path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "classes_": self.classes_,
                "feature_cols": self.feature_cols
            }, f)
        print(f"✅ Model saved to {path}")

    def load_model(self, path="rf_model.pkl"):
        if not os.path.exists(path):
            print(f"❌ Model file {path} not found.")
            return
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.model = data["model"]
            self.classes_ = data["classes_"]
            self.feature_cols = data["feature_cols"]
        self.trained = True
        print(f"✅ Model loaded from {path}")

    def predict(self, row):
        missing_cols = [col for col in self.feature_cols if col not in row]
        if missing_cols or row[self.feature_cols].isnull().any():
            return "NEUTRAL"

        x_input = pd.DataFrame([row[self.feature_cols]])
        probs = self.model.predict_proba(x_input)[0]

        confidence = max(probs)
        predicted_class = self.classes_[np.argmax(probs)]

        if confidence < CONFIDENCE_THRESHOLD:
            return "NEUTRAL"
        return predicted_class

    def predict_all(self, df):
        df = df.copy()
        df["rf_prediction"] = "NEUTRAL"
        df["rf_confidence"] = 0.0  # New column

        valid = df[self.feature_cols].notnull().all(axis=1)
        if valid.sum() == 0:
            return df

        X = df.loc[valid, self.feature_cols]
        probs = self.model.predict_proba(X)
        classes = self.model.classes_

        preds = []
        confs = []
        for p in probs:
            confidence = max(p)
            label = classes[np.argmax(p)]
            if confidence >= CONFIDENCE_THRESHOLD:
                preds.append(label)
                confs.append(confidence)
            else:
                preds.append("NEUTRAL")
                confs.append(0)

        df.loc[valid, "rf_prediction"] = preds
        df.loc[valid, "rf_confidence"] = confs
        return df


def draw_threshold_graph(screen, y_val, y_probs, classes):
    font = pygame.font.SysFont("arial", 14)
    screen.fill((255, 255, 255))
    thresholds = [i / 100 for i in range(30, 100, 5)]
    spacing = 500 // len(thresholds)
    base_x = 50
    base_y = 350
    max_height = 200
    clock = pygame.time.Clock()
    for idx, threshold in enumerate(thresholds):
        y_pred = []
        for probs in y_probs:
            confidence = max(probs)
            pred_class = classes[np.argmax(probs)]
            y_pred.append(pred_class if confidence >= threshold else "NEUTRAL")

        report = classification_report(
            y_val,
            y_pred,
            labels=["BUY", "SELL", "NEUTRAL"],
            output_dict=True,
            zero_division=0
        )

        x = base_x + idx * spacing

        def draw_bar(metric, color, offset):
            value = report.get(metric, {}).get("recall", 0)
            h = int(value * max_height)
            pygame.draw.rect(screen, color, (x + offset, base_y - h, 4, h))

        draw_bar("BUY", (0, 200, 0), -6)  # Green: recall BUY
        draw_bar("SELL", (0, 0, 200), 0)  # Blue: recall SELL

        value = report.get("BUY", {}).get("precision", 0)
        h = int(value * max_height)
        pygame.draw.rect(screen, (255, 150, 0), (x + 6, base_y - h, 4, h))  # Orange: precision BUY

        value = report.get("SELL", {}).get("precision", 0)
        h = int(value * max_height)
        pygame.draw.rect(screen, (150, 0, 150), (x + 12, base_y - h, 4, h))  # Purple: precision SELL
        for i in range(2, 10):
            line_h = base_y - (max_height * (i/10))
            pygame.draw.line(screen, (0,0,0), (base_x-40, line_h), (580, line_h), 1)
            label = f"{i*10}%"
            text = font.render(label, True, (0, 0, 0))
            screen.blit(text, (base_x-40, line_h-12))
        pygame.draw.rect(screen, (0, 0, 0), (base_x-40, base_y-max_height, 580, max_height), 1)
        threshold_label = font.render(str(int(threshold * 100)), True, (0, 0, 0))
        screen.blit(threshold_label, (x, base_y + 5))

    legend = [
        ("BUY Recall", (0, 200, 0)),
        ("SELL Recall", (0, 0, 200)),
        ("BUY Precision", (255, 150, 0)),
        ("SELL Precision", (150, 0, 150)),
    ]
    for i, (label, color) in enumerate(legend):
        pygame.draw.rect(screen, color, (420, 30 + i * 20, 10, 10))
        text = font.render(label, True, (0, 0, 0))
        screen.blit(text, (435, 28 + i * 20))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        pygame.display.flip()
        clock.tick(30)


def recreate_model(screen):
    clf = RandomForestSignalClassifier()
    formatted_data = load_backtest_data()
    clf.train(formatted_data, screen)
    clf.save_model("main_rf.pkl")

