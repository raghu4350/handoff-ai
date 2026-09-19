import requests

def main():
    try:
        with open("HandoffAI_Interview_Guide.md", "r", encoding="utf-8") as f:
            markdown = f.read()
        
        print("Sending to PDF conversion API...")
        response = requests.post(
            "https://md-to-pdf.fly.dev",
            data={"markdown": markdown},
            timeout=30
        )
        
        if response.status_code == 200:
            with open("HandoffAI_Interview_Guide.pdf", "wb") as f:
                f.write(response.content)
            print("SUCCESS: HandoffAI_Interview_Guide.pdf created!")
        else:
            print("FAILED with status:", response.status_code)
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main()
