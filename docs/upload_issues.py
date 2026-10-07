#!/usr/bin/env python3
"""
Скрипт для автоматической загрузки 60 Use Cases в GitHub Issues.
Поддерживает два режима работы:
1. Через утилиту GitHub CLI (gh issue create) — самый простой способ.
2. Через GitHub REST API с использованием Personal Access Token.
"""

import os
import re
import sys
import subprocess
import json

USE_CASES_FILE = os.path.join(os.path.dirname(__file__), "60_USE_CASES.md")


def parse_use_cases(filepath):
    """Парсит markdown файл и извлекает список 60 сценариев"""
    cases = []
    pattern = re.compile(r"^(\d+)\.\s+(\[MVP\]\s+)?\*\*(Как [^*]+)\*\*,\s*(я хочу иметь возможность [^.]+)\.?$")
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            match = pattern.match(line)
            if match:
                num = match.group(1)
                is_mvp = bool(match.group(2))
                role_part = match.group(3)
                action_part = match.group(4)
                
                title = f"UC-{num}: {role_part}, {action_part}"
                if len(title) > 90:
                    title = title[:87] + "..."
                
                body = (
                    f"### Описание Use Case\n\n"
                    f"**Номер:** #{num}\n\n"
                    f"**Формулировка:**\n> {line}\n\n"
                    f"**Статус:** {'⭐ MVP (Минимальный функционал)' if is_mvp else 'Расширенный функционал'}\n"
                )
                
                labels = ["use-case"]
                if is_mvp:
                    labels.append("MVP")
                    
                cases.append({
                    "number": int(num),
                    "title": f"UC-{num}: {line[line.find('**')+2:line.rfind('**')]}",
                    "full_text": line,
                    "is_mvp": is_mvp,
                    "labels": labels,
                    "body": body
                })
    return cases


def upload_via_gh_cli(cases):
    """Загрузка через официальный GitHub CLI (gh)"""
    print("Проверка наличия GitHub CLI (gh)...")
    try:
        subprocess.run(["gh", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        print("GitHub CLI (gh) не найден в системе. Переключение на API.")
        return False

    print(f"Найдено {len(cases)} сценариев. Начинаем загрузку в текущий репозиторий через gh...")
    for c in cases:
        labels_str = ",".join(c["labels"])
        cmd = [
            "gh", "issue", "create",
            "--title", f"UC-{c['number']}: {c['full_text'][:70]}...",
            "--body", c["body"],
            "--label", labels_str
        ]
        try:
            res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            print(f"[OK] Создан Issue #{c['number']}: {res.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"[ОШИБКА] Не удалось создать #{c['number']}: {e.stderr.strip()}")
    return True


def upload_via_api(cases, repo, token):
    """Загрузка через GitHub REST API"""
    import urllib.request
    import urllib.error

    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "CalorieTracker-IssueUploader"
    }

    print(f"Загрузка {len(cases)} сценариев в репозиторий {repo} через GitHub API...")
    for c in cases:
        data = {
            "title": f"UC-{c['number']}: {c['full_text'][:70]}...",
            "body": c["body"],
            "labels": c["labels"]
        }
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                print(f"[OK] Создан Issue #{c['number']} (URL: {resp_data.get('html_url')})")
        except urllib.error.HTTPError as e:
            print(f"[ОШИБКА] Ошибка API на #{c['number']}: {e.code} - {e.read().decode('utf-8')}")


def main():
    if not os.path.exists(USE_CASES_FILE):
        print(f"Файл {USE_CASES_FILE} не найден.")
        return

    cases = parse_use_cases(USE_CASES_FILE)
    print(f"Успешно распознано {len(cases)} сценариев (MVP: {sum(1 for c in cases if c['is_mvp'])}).")

    # Сначала пробуем gh CLI
    if upload_via_gh_cli(cases):
        print("\nВсе сценарии успешно загружены в GitHub Issues!")
        return

    # Если gh CLI нет или не авторизован, запрашиваем параметры API
    print("\nДля ручной загрузки через GitHub API укажите:")
    repo = input("Репозиторий (в формате username/repo): ").strip()
    token = input("GitHub Personal Access Token (classic or fine-grained): ").strip()

    if repo and token:
        upload_via_api(cases, repo, token)
        print("\nЗагрузка завершена!")
    else:
        print("Параметры не указаны. Загрузка отменена.")


if __name__ == "__main__":
    main()
