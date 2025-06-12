import requests

STRUCTURE_ID = 1046831245129
TARGET_TYPE_ID = 62622
BEARER_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkpXVC1TaWduYXR1cmUtS2V5IiwidHlwIjoiSldUIn0.eyJzY3AiOiJlc2ktbWFya2V0cy5zdHJ1Y3R1cmVfbWFya2V0cy52MSIsImp0aSI6IjIwMzcwMjZhLWU2NDAtNDgwNi04NDI1LTNiYTk0ZDRlZDFmMCIsImtpZCI6IkpXVC1TaWduYXR1cmUtS2V5Iiwic3ViIjoiQ0hBUkFDVEVSOkVWRToyMTEzMjg5NDk5IiwiYXpwIjoiNzgzMTdiOGFiZWY4NDU0YmFmYzUzZTIwMzYzMWE5ODAiLCJ0ZW5hbnQiOiJ0cmFucXVpbGl0eSIsInRpZXIiOiJsaXZlIiwicmVnaW9uIjoid29ybGQiLCJhdWQiOlsiNzgzMTdiOGFiZWY4NDU0YmFmYzUzZTIwMzYzMWE5ODAiLCJFVkUgT25saW5lIl0sIm5hbWUiOiJOYXJpb2QgTmFyZW4iLCJvd25lciI6ImYzdGZ3NEE4VTdRRTVhcmZPeEkyR0NVdWJCVT0iLCJleHAiOjE3NDk3MTkyMDksImlhdCI6MTc0OTcxODAwOSwiaXNzIjoiaHR0cHM6Ly9sb2dpbi5ldmVvbmxpbmUuY29tIn0.DahdWJBEfVO_VDqmN355gH4ghlkibP_MycTMwptuJy2PP8y8AxqmU3QbOqIzxdA9q4TzeV2hoAPdEWN_dHaSCAzHF0_CCRLPo1Uw-4UGtSQID8PalBzqB5OIHOLzqsYJQKWRsn5Q4hLR_8RDfKTFIDC9eQs5UYFW6DUeFW7KBvVRsGOT2gsTerbTLbCSrq8cxVJV7OrRnUdKmYUFA3tfQ5k5CyhyQebWYLjvIM6P6piImGRdYzwBOKHLQ4F68SR0222t1RcXFtOlGKaiE0w6STo0SlgIWM803WeNWQHdBfUEF-B8Qf5Lc-BjEqPTaRm9ytw-rC-ywOIBny7dNm7SJg"  # Replace with your real token

headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

page = 1
all_orders = []

print(f"Fetching market orders from structure {STRUCTURE_ID}...")

while True:
    url = f"https://esi.evetech.net/latest/markets/structures/{STRUCTURE_ID}/?page={page}"
    response = requests.get(url, headers=headers)

    if response.status_code == 403:
        print("403 Forbidden: No access to this structure's market data.")
        break
    elif response.status_code == 500:
        print(f"500 Server Error on page {page} — assuming end of data.")
        break

    response.raise_for_status()
    orders = response.json()

    if not orders:
        break

    all_orders.extend(orders)
    print(f"Fetched page {page} with {len(orders)} orders.")

    if len(orders) < 1000:
        break  # Last page

    page += 1

print(f"\nScanning {len(all_orders)} orders for type_id {TARGET_TYPE_ID}...")

found = False
for order in all_orders:
    if not order['is_buy_order'] and order['type_id'] == TARGET_TYPE_ID:
        print(f"\n✅ FOUND: {order['volume_remain']}x @ {order['price']} ISK")
        found = True

if not found:
    print("❌ No sell orders for Large Asteroid Ore Compressor I found in this structure.")