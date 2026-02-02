import requests
import json
import time

# ================= 配置区 =================
GIST_ID = "你的_GIST_ID"
GH_TOKEN = "你的_GITHUB_TOKEN"
FUND_CODE = "005844" 
# =========================================

def get_holdings_danjuan(code):
    """
    方案 C: 使用蛋卷基金 (雪球) 接口
    特点: JSON 格式极度规范，很少 404
    """
    # 蛋卷的基金详情接口
    url = f"https://danjuanfunds.com/djapi/fund/detail/{code}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://danjuanfunds.com",
        "Referer": f"https://danjuanfunds.com/funding/{code}"
    }
    
    try:
        print(f"📡 正在从蛋卷基金请求 {code} ...")
        resp = requests.get(url, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            print(f"❌ 请求失败: Status {resp.status_code}")
            return []

        data = resp.json()
        
        # 蛋卷的数据结构: data -> fund_position -> stock_list
        # 注意: 蛋卷可能没有 fund_position 字段（如果是新基金），做个保护
        fund_data = data.get("data", {})
        position = fund_data.get("fund_position", {})
        stock_list = position.get("stock_list", [])
        
        if not stock_list:
            print("⚠️ 警告: 蛋卷返回的持仓列表为空 (可能未披露或代码错误)")
            print(f"调试信息: {str(fund_data.keys())}")
            return []

        holdings = []
        for item in stock_list:
            # 蛋卷返回: name, code (如 "688012"), percent (如 9.23)
            name = item['name']
            raw_code = item['code']
            weight = float(item['percent'])
            
            # 格式化代码
            prefix = "sh" if raw_code.startswith(('6', '9')) else "sz"
            formatted_code = f"{prefix}{raw_code}"
            
            holdings.append({
                "name": name,
                "code": formatted_code,
                "weight": weight
            })
            
        print(f"✅ 成功获取 {len(holdings)} 只持仓股票！(数据源: 蛋卷)")
        return holdings

    except Exception as e:
        print(f"❌ 异常: {e}")
        return []

def update_gist(holdings):
    if not holdings:
        print("❌ 数据为空，放弃上传 Gist。")
        return
    
    url = f"https://api.github.com/gists/{GIST_ID}"
    headers = {
        "Authorization": f"token {GH_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    
    payload = {
        "description": f"Fund {FUND_CODE} Holdings (Updated: {current_time})",
        "files": {
            "fund_holdings.json": {
                "content": json.dumps({
                    "update_time": current_time,
                    "source": "danjuan",
                    "holdings": holdings
                }, ensure_ascii=False, indent=2)
            }
        }
    }
    
    try:
        print("☁️ 正在上传到 GitHub Gist...")
        r = requests.patch(url, headers=headers, json=payload)
        if r.status_code == 200:
            print("🎉 成功！Scriptable 现在可以读取了。")
        else:
            print(f"⚠️ Gist 更新失败: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"上传异常: {e}")

if __name__ == "__main__":
    data = get_holdings_danjuan(FUND_CODE)
    update_gist(data)