import urequests as requests
import os

# 配置
VERSION_FILE_PATH = "version"  # 存储本地版本号的目录
VERSION_JSON_URL = "https://github.com/Starrynight252/IC_ROBOT_OTA/blob/main/version.json"

# 确保版本目录存在
def ensure_version_dir():
    if VERSION_FILE_PATH not in os.listdir():
        os.mkdir(VERSION_FILE_PATH)

# 获取本地文件的版本
def get_local_version(filename):
    try:
        with open(f"{VERSION_FILE_PATH}/{filename}.ver", "r") as f:
            return f.read().strip()
    except OSError:
        print(f"[WARN] {filename}.ver 文件不存在或无法访问")
        return ""  # 本地文件版本不存在时返回空字符串
    except Exception as e:
        print(f"[ERROR] 获取 {filename} 本地版本失败: {e}")
        return ""  # 如果有其他异常，返回空字符串

# 保存本地文件的版本
def save_local_version(filename, version):
    try:
        with open(f"{VERSION_FILE_PATH}/{filename}.ver", "w") as f:
            f.write(version)
        print(f"[INFO] 本地版本已保存: {filename} => {version}")
    except Exception as e:
        print(f"[ERROR] 保存 {filename} 本地版本失败: {e}")

# 下载文件并保存
def download_and_save_file(filename, url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            with open(filename, "w") as f:
                f.write(r.text)
            print(f"[INFO] {filename} 下载并保存成功")
            return True
        else:
            print(f"[ERROR] 下载失败，HTTP 状态码: {r.status_code}")
            return False
    except Exception as e:  # ✅ MicroPython only supports Exception, not RequestException
        print(f"[ERROR] 下载 {filename} 时出错:", e)
    return False

# 主更新逻辑
def update_all_from_version_json():
    ensure_version_dir()

    try:
        r = requests.get(VERSION_JSON_URL)
        if r.status_code != 200:
            print("[ERROR] 获取 version.json 失败")
            return
        version_info = r.json()  # 解析 version.json
    except Exception as e:
        print("[ERROR] 解析 version.json 失败:", e)
        return

    for filename, meta in version_info.items():
        # 防止更新 pyota.py
        if filename == "pyota.py":
            print("[INFO] pyota.py 无需更新，跳过")
            continue

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




def run():
    print("pyota 已被调用")
    update_all_from_version_json()


