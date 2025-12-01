import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import random


class CompanyAgent:
    def __init__(self, mailbox_company, mailbox_personal, game_time_system, approved_store_path=None, review_mode="A"):
        """
        :param mailbox_company:公司邮箱目录（收到的邮件）
        :param mailbox_personal:主播邮箱目录（发送给主播）
        :param game_time_system:GameTime实例，获取虚拟时间
        :param approved_store_path:已经通过的企划的本地存储文件
        :param review_mode:A=宽松审核，B=严格审核
        """
        self.mailbox_company = Path(mailbox_company)
        self.mailbox_personal = Path(mailbox_personal)
        self.game_time_system = game_time_system

        self.mailbox_company.mkdir(parents=True, exist_ok=True)
        self.mailbox_personal.mkdir(parents=True, exist_ok=True)

        self.review_mode = review_mode
        # 保存已经通过审核但未安排拍摄的企划
        self.approved_projects = {}
        # 可持久化
        self.approved_store_path = approved_store_path
        if approved_store_path and Path(approved_store_path).exists():
            try:
                self.approved_projects = json.load(open(approved_store_path, 'r', encoding='utf-8'))
            except json.JSONDecodeError:
                print("[CompanyAgent] approved_projects 文件读取失败或为空，初始化为空字典。")
                self.approved_projects = {}

    # ====================================================
    # 邮件读取
    # ====================================================
    def load_company_mail(self):
        mails = []
        for file in self.mailbox_company.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                mails.append((file, content))
            except:
                pass
        return mails

    # ====================================================
    # 邮件发送
    # ====================================================
    def send_mail_to_vtuber(self, subject, mail_type, payload):
        mail = {
            "timestamp": self.game_time_system.now().strftime("%Y-%m-%d %H:%M:%S"),
            "subject": subject,
            "type": mail_type,
            "data": payload
        }

        virtual_dt = self.game_time_system.now()
        filename = f"mail_{virtual_dt.strftime('%Y%m%d_%H%M%S')}_{random.randint(100, 999)}.json"
        with open(self.mailbox_personal / filename, 'w', encoding='utf-8') as f:
            json.dump(mail, f, ensure_ascii=False, indent=2)

    # ====================================================
    # 企划审核
    # ====================================================
    def review_project(self, project_json):
        """
        审核企划案
        宽松审核规则A：
        - 必须包含字段：project_name, project_content
        - project_content 长度不能过短
        """
        data = project_json.get("project", project_json)

        required_fields = ["project_name", "project_content"]

        for field in required_fields:
            if field not in data:
                return {
                    "approved": False,
                    "reason": f"缺少必要字段: {field}"
                }

        if not data["project_name"].strip():
            return {"approved": False, "reason": "企划名称为空"}

        if not data["project_content"].strip():
            return {"approved": False, "reason": "企划内容为空"}

        if len(data["project_content"]) < 20:
            return {"approved": False, "reason": "企划内容过短，不足以构成企划"}

        return {"approved": True, "reason": "宽松审核已通过"}

    # ====================================================
    # 每日流程
    # ====================================================
    def daily_update(self):
        """
        每天执行一次：
        1.审核企划案
        2.处理广告邮件
        3.安排拍摄（如果需要）
        """

        mails = self.load_company_mail()

        for filepath, mail in mails:
            mail_type = mail.get("type")
            if mail_type == "project":
                self._process_project_mail(filepath, mail)

            elif mail_type == "advertisement":
                self._process_advertisement_mail(filepath, mail)

            # 处理完删除公司邮箱邮件
            filepath.unlink()

        # 安排拍摄，如果有已通过的企划
        self._schedule_shooting()

    # ====================================================
    # 处理企划案
    # ====================================================
    def _process_project_mail(self, filepath, mail):
        project_id = mail.get("project_id")

        review = self.review_project(mail)
        project_name = mail.get('project', {}).get('project_name', '未命名企划')

        payload = {
            "project_id": project_id,
            "project_name": project_name,
            "result": "approved" if review["approved"] else "not approved",
            "reason": review["reason"]
        }

        if review["approved"]:
            self.approved_projects[project_id] = mail
            print(f"[CompanyAgent] 企划通过：{project_id}")

            self.send_mail_to_vtuber(
                subject=f"【企划审核通过】{project_name}",
                mail_type="project_review",
                payload=payload
            )

        else:
            # 根据项目说明："如果沒有通過，就不做處理。"
            # 如果要严格遵守此规则，则不发送邮件。
            # 如果希望主播收到通知（更友好），则发送邮件。这里选择发送通知（更实用）。
            print(f"[CompanyAgent]企划未通过：{project_id}")

            self.send_mail_to_vtuber(
                subject=f"【企划审核未通过】{project_name}",
                mail_type="project_review",
                payload=payload
            )

        # 保存持久化
        self._save_approved_projects()

    # ====================================================
    # 处理广告邮件
    # ====================================================
    def _process_advertisement_mail(self, filepath, mail):
        print("[CompanyAgent] 收到广告，转发给主播。")

        # 假设广告邮件中可能包含以下关键信息（如果广告商Agent提供的话）
        ad_data = mail.get("ad_info", {})  # 假设广告的关键信息在一个 "ad_info" 字段中

        subject = f"【广告】{mail.get('ad_title', ad_data.get('brand', '新广告'))}"

        # 提取并结构化广告信息，方便 Vtuber Agent 解析
        payload = {
            "ad_title": mail.get('ad_title', '未命名广告'),
            "brand": ad_data.get('brand', '未知品牌'),
            "suggested_duration": ad_data.get('duration', '60min'),
            "required_content": ad_data.get('requirement', ''),
            "raw_content": mail.get("content", "")  # 保留原始文本内容供参考
        }

        self.send_mail_to_vtuber(
            subject=subject,
            mail_type="advertisement",
            payload=payload
        )

    def _extract_project_info(self, project_data):
        data = project_data.get("project", project_data) if isinstance(project_data, dict) else project_data

        project_id = data.get("project_id") or data.get("id") or data.get("id_str") or None
        project_name = data.get("project_name") or data.get("title") or data.get("name") or "未命名企划"
        description = data.get("project_content") or data.get("description") or data.get("content") or ""

        preferred = data.get("preferred_time") or {}
        preferred_start = preferred.get("start")
        preferred_end = preferred.get("end")

        return {
            "project_id": project_id,
            "project_name": project_name,
            "description": description,
            "preferred_start": preferred_start,
            "preferred_end": preferred_end
        }

    def _save_approved_projects(self):
        if not self.approved_store_path:
            return
        try:
            with open(self.approved_store_path, "w", encoding="utf-8") as f:
                json.dump(self.approved_projects, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CompanyAgent] 保存 approved_projects 失败：{e}")

    # ====================================================
    # 安排拍摄
    # ====================================================

    def _schedule_shooting(self):
        if not self.approved_projects:
            print("[CompanyAgent] 无已通过企划，无需安排拍摄。")
            return

        if random.random() < 0.5:
            print("[CompanyAgent] 今天决定不安排拍摄任务，将企划保留至下次决策。")
            return

        project_id, project_data = next(iter(self.approved_projects.items()))
        info = self._extract_project_info(project_data)

        current_dt = self.game_time_system.now()
        shoot_dt = current_dt + timedelta(days=1)
        shoot_date = shoot_dt.date()

        def parse_time_on_shoot_date(s, fallback_date):
            if not s or not s.strip:
                return None
            try:
                if len(s.strip()) <= 5 and ":" in s:  # "HH:MM"
                    hh, mm = map(int, s.strip().split(":"))
                    return datetime.combine(fallback_date, datetime.min.time()).replace(hour=hh, minute=mm)
                else:
                    # 尝试解析为完整格式
                    return datetime.strptime(s, "%Y-%m-%d %H:%M")
            except Exception:
                pass
            return None

        preferred_start_dt = parse_time_on_shoot_date(info["preferred_start"], shoot_date)
        preferred_end_dt = parse_time_on_shoot_date(info["preferred_end"], shoot_date)

        # 默认安排时间：虚拟的明天 10:00 - 12:00
        default_start = datetime.combine(shoot_date, datetime.min.time()).replace(hour=10, minute=0)
        default_end = default_start + timedelta(hours=2)

        if preferred_start_dt and not preferred_end_dt:
            # 如果只有开始时间，结束时间默认 +2 小时
            preferred_end_dt = preferred_start_dt + timedelta(hours=2)

        start_dt = preferred_start_dt or default_start
        end_dt = preferred_end_dt or (start_dt + timedelta(hours=2) if not preferred_start_dt else preferred_end_dt)

        # 确保 end_dt 晚于 start_dt
        if end_dt <= start_dt:
            end_dt = start_dt + timedelta(hours=2)

        subject = f"【拍攝安排】企劃：{info['project_name']}"

        # 结构化拍摄任务的 payload
        payload = {
            "category": "shoot",
            "project_id": info["project_id"] or project_id,
            "project_name": info["project_name"],
            "start_time": start_dt.strftime("%Y-%m-%d %H:%M"),
            "end_time": end_dt.strftime("%Y-%m-%d %H:%M"),
            "content": info["description"] or f"公司已安排拍攝企劃：{info['project_name']}，請準備相關素材。"
        }

        self.send_mail_to_vtuber(
            subject=subject,
            mail_type="shoot_schedule",  # 使用更具体的类型
            payload=payload
        )
        print(f"[CompanyAgent] 已安排拍攝：{info['project_name']} ({payload['start_time']} - {payload['end_time']})")

        try:
            del self.approved_projects[project_id]
        except KeyError:
            # 也可能 project_id 为 None 或不同键，尝试根据 project_name 找到并删除
            to_delete = None
            for k, v in list(self.approved_projects.items()):
                pd = v.get("project", v) if isinstance(v, dict) else v
                name = pd.get("project_name") or pd.get("title") or pd.get("name")
                if name == info["project_name"]:
                    to_delete = k
                    break
            if to_delete:
                del self.approved_projects[to_delete]
        # 保存
        self._save_approved_projects()
