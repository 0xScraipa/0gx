from flask import Flask, Response
import requests
import json
import pandas as pd
import torch
from chronos import ChronosPipeline

app = Flask(__name__)
model_name = "amazon/chronos-t5-tiny"
try:
    pipeline = ChronosPipeline.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype=torch.bfloat16,
    )
except Exception as e:
    pipeline = None
    print(f"Failed to load pipeline: {e}")

def get_binance_url(symbol="ETHUSDT", interval="1m", limit=1000):
    return f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

@app.route("/inference/<string:token>")
def get_inference(token):
    if pipeline is None:
        return Response(json.dumps({"error": "Pipeline is not available"}), status=500, mimetype='application/json')

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
        
        if symbol in ['BTCUSDT', 'SOLUSDT']:
            df = df.tail(10)  # 10mins BTCUSDT và SOLUSDT
        else:
            df = df.tail(20)  # 20mins
    else:
        return Response(json.dumps({"Failed to retrieve data from Binance API": str(response.text)}), 
                        status=response.status_code, 
                        mimetype='application/json')

    context = torch.tensor(df["price"].values)
    prediction_length = len(df)  # Sử dụng số lượng phút tương ứng với dữ liệu đã chọn

    try:
        forecast = pipeline.predict(context, prediction_length)
        forecast_mean = forecast[0].mean().item()  # Tính giá trị trung bình
        return Response(str(forecast_mean), status=200, mimetype='text/plain')
    except Exception as e:
        return Response(str(e), status=500, mimetype='text/plain')

# Chạy Flask app
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
