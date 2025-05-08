import urequests as requests
import os

# 配置
VERSION_FILE_PATH = "version"  # 存储本地版本号的目录
VERSION_JSON_URL = "http://192.168.237.122:1080/espbin/version.json"

# 确保版本目录存在
def ensure_version_dir():
    if VERSION_FILE_PATH not in os.listdir():
        os.mkdir(VERSION_FILE_PATH)

# 获取本地文件的版本
def get_local_version(filename):
    try:
        with open(f"{VERSION_FILE_PATH}/{filename}.ver", "r") as f:
            return f.read().strip()
    except:
        return ""

# 保存本地文件的版本
def save_local_version(filename, version):
    with open(f"{VERSION_FILE_PATH}/{filename}.ver", "w") as f:
        f.write(version)

# 下载文件并保存
def download_and_save_file(filename, url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            with open(filename, "w") as f:
                f.write(r.text)
            return True
    except Exception as e:
        print(f"[ERROR] 下载 {filename} 失败:", e)
    return False

# 主更新逻辑
def update_all_from_version_json():
    ensure_version_dir()

    try:
        r = requests.get(VERSION_JSON_URL)
        if r.status_code != 200:
            print("[ERROR] 获取 version.json 失败")
            return
        version_info = r.json()
    except Exception as e:
        print("[ERROR] 解析 version.json 失败:", e)
        return

    for filename, meta in version_info.items():
        remote_version = meta.get("version", "")
        url = meta.get("url", "")
        if not remote_version or not url:
            print(f"[WARN] 跳过无效条目: {filename}")
            continue

        local_version = get_local_version(filename)

        if local_version != remote_version:
            print(f"[INFO] 检测到 {filename} 有更新: 本地版本={local_version}, 远程版本={remote_version}")
            if download_and_save_file(filename, url):
                save_local_version(filename, remote_version)
                print(f"[OK] {filename} 更新完成")
            else:
                print(f"[FAIL] {filename} 更新失败")
        else:
            print(f"[OK] {filename} 无需更新（版本一致）")

