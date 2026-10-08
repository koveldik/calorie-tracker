cat << 'EOF' > docs/fix_mvp_labels.py
import urllib.request
import urllib.error
import json
import time

def main():
    repo = input("Введите репозиторий (например, koveldik/calorie-tracker): ").strip()
    token = input("Введите GitHub Personal Access Token: ").strip()

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "CalorieTracker-LabelFixer"
    }

    label_url = f"https://api.github.com/repos/{repo}/labels"
    label_data = json.dumps({
        "name": "MVP",
        "color": "e11d48",
        "description": "Ключевой сценарий MVP"
    }).encode("utf-8")

    req = urllib.request.Request(label_url, data=label_data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            print("[+] Лейбл 'MVP' успешно создан в репозитории.")
    except urllib.error.HTTPError as e:
        if e.code == 422:
            print("[i] Лейбл 'MVP' уже существует в репозитории.")
        else:
            print(f"[!] Ошибка при создании лейбла: {e.code}")

    print("[*] Получение списка issues из GitHub...")
    issues = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo}/issues?state=all&per_page=100&page={page}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if not data:
                    break
                issues.extend(data)
                page += 1
        except Exception as e:
            print(f"[!] Ошибка получения списка: {e}")
            break

    print(f"[*] Найдено всего issues: {len(issues)}")

    mvp_numbers = {1, 2, 4, 7, 8, 9, 10, 11, 13, 15, 20, 21, 22, 23, 24, 25, 26, 31, 51, 52}

    updated_count = 0
    for issue in issues:
        title = issue.get("title", "")
        body = issue.get("body", "")
        labels = [l.get("name") for l in issue.get("labels", [])]

        is_mvp = False
        if "[MVP]" in title or "[MVP]" in body:
            is_mvp = True

        for num in mvp_numbers:
            if f"UC-{num}:" in title or f"UC-{num:02d}:" in title or f"{num}." in title:
                is_mvp = True
                break

        if is_mvp and "MVP" not in labels:
            issue_number = issue["number"]
            patch_url = f"https://api.github.com/repos/{repo}/issues/{issue_number}/labels"
            patch_data = json.dumps({"labels": ["MVP"]}).encode("utf-8")
            req = urllib.request.Request(patch_url, data=patch_data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req) as resp:
                    print(f"[+] Добавлен лейбл MVP к Issue #{issue_number}: {title[:40]}...")
                    updated_count += 1
                    time.sleep(0.8)
            except Exception as e:
                print(f"[!] Ошибка обновления Issue #{issue_number}: {e}")

    print(f"\n[✓] Готово! Лейбл MVP добавлен к {updated_count} тикетам.")

if __name__ == "__main__":
    main()
EOF
