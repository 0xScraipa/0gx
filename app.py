import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import requests
from flask import Flask, Response, json

app = Flask(__name__)

# Define the HybridModel (same as in your model.py)
class HybridModel(nn.Module):
    def __init__(self, input_size, hidden_layer_size, output_size, num_layers, dropout):
        super(HybridModel, self).__init__()
        self.hidden_layer_size = hidden_layer_size
        self.num_layers = num_layers
        
        # LSTM layer
        self.lstm = nn.LSTM(input_size, hidden_layer_size, num_layers=num_layers, 
                            dropout=dropout, batch_first=True)
        
        # GRU layer
        self.gru = nn.GRU(hidden_layer_size, hidden_layer_size, num_layers=num_layers, 
                          dropout=dropout, batch_first=True)
        
        # Linear layer
        self.linear = nn.Linear(hidden_layer_size, output_size)
        
        self.hidden_cell = (torch.zeros(num_layers, 1, self.hidden_layer_size),
                            torch.zeros(num_layers, 1, self.hidden_layer_size))

    def forward(self, input_seq):
        # Pass through LSTM
        lstm_out, self.hidden_cell = self.lstm(input_seq, self.hidden_cell)
        
        # Pass through GRU
        gru_out, _ = self.gru(lstm_out)
        
        # Final prediction
        predictions = self.linear(gru_out[:, -1])
        return predictions

# Load the trained model
device = torch.device("cpu")

# Use the same parameters as in model.py
model = HybridModel(input_size=1, hidden_layer_size=155, output_size=1, num_layers=3, dropout=0.3)
model.load_state_dict(torch.load("hybrid_lstm_gru_model_optimized.pth", map_location=device), strict=False)
model.eval()


# Function to fetch historical data from Binance
def get_binance_url(symbol="ETHUSDT", interval="1m", limit=1000):
    return f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

@app.route("/inference/<string:token>")
def get_inference(token):
    if model is None:
        return Response(json.dumps({"error": "Model is not available"}), status=500, mimetype='application/json')

    symbol_map = {
        'ETH': 'ETHUSDT',
        'BTC': 'BTCUSDT',
        'BNB': 'BNBUSDT',
        'SOL': 'SOLUSDT',
        'ARB': 'ARBUSDT'
    }

    token = token.upper()
    if token in symbol_map:
        symbol = symbol_map[token]
    else:
        return Response(json.dumps({"error": "Unsupported token"}), status=400, mimetype='application/json')

    url = get_binance_url(symbol=symbol)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        df["close_time"] = pd.to_datetime(df["close_time"], unit='ms')
        df = df[["close_time", "close"]]
        df.columns = ["date", "price"]
        df["price"] = df["price"].astype(float)

        # Adjust the number of rows based on the symbol
        if symbol in ['BTCUSDT', 'SOLUSDT']:
            df = df.tail(10)  # Use last 10 minutes of data
        else:
            df = df.tail(20)  # Use last 20 minutes of data

        # Prepare data for the LSTM model
        scaler = MinMaxScaler(feature_range=(-1, 1))
        scaled_data = scaler.fit_transform(df['price'].values.reshape(-1, 1))

        seq = torch.FloatTensor(scaled_data).view(1, -1, 1)

        # Reset LSTM-GRU hidden state
        model.hidden_cell = (torch.zeros(model.num_layers, 1, model.hidden_layer_size),
                             torch.zeros(model.num_layers, 1, model.hidden_layer_size))

        # Make prediction
        with torch.no_grad():
            y_pred = model(seq)

        # Inverse transform the prediction to get the actual price
        predicted_price = scaler.inverse_transform(y_pred.numpy())

        # Round the predicted price to 2 decimal places
        rounded_price = round(predicted_price.item(), 2)

        # Return the rounded price as a string
        return Response(str(rounded_price), status=200, mimetype='application/json')
    else:
        return Response(json.dumps({"error": "Failed to retrieve data from Binance API", "details": response.text}), 
                        status=response.status_code, 
                        mimetype='application/json')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
