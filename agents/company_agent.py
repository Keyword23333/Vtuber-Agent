import os
import json
from datetime import datetime, timedelta
from pathlib import Path


class CompanyAgent:
    def __init__(self, mailbox_company, mailbox_personal, approved_store_path=None, review_mode="A"):
        """
        :param mailbox_company:公司邮箱目录（收到的邮件）
        :param mailbox_personal:主播邮箱目录（发送给主播）
        :param approved_store_path:已经通过的企划的本地存储文件
        :param review_mode:A=宽松审核，B=严格审核
        """
        self.mailbox_company = Path(mailbox_company)
        self.mailbox_personal = Path(mailbox_personal)

        self.mailbox_company.mkdir(parents=True, exist_ok=True)
        self.mailbox_personal.mkdir(parents=True, exist_ok=True)

        self.review_mode = review_mode
        # 保存已经通过审核但未安排拍摄的企划
        self.approved_projects = {}
        # 可持久化
        self.approved_store_path = approved_store_path
        if approved_store_path and Path(approved_store_path).exists():
            self.approved_projects = json.load(open(approved_store_path, 'r', encoding='utf-8'))

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
    def send_mail_to_vtuber(self, subject, content):
        mail = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "subject": subject,
            "content": content
        }

        filename = f"mail_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
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
                self._process_advertisement_mail(mail)

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
        if review["approved"]:
            self.approved_projects[project_id] = mail
            print(f"[CompanyAgent] 企划通过：{project_id}")

            self.send_mail_to_vtuber(
                subject=f"【企划审核通过】{mail.get('project', {}).get('project_name', '')}",
                content={
                    "project_id": project_id,
                    "result": "approved",
                    "reason": review["reason"]
                }
            )

        else:
            print(f"[CompanyAgent]企划未通过：{project_id}")

            self.send_mail_to_vtuber(
                subject=f"【企划审核未通过】{mail.get('project', {}).get('project_name', '')}",
                content={
                    "project_id": project_id,
                    "result": "not approved",
                    "reason": review["reason"]
                }
            )

        # 保存持久化
        if self.approved_store_path:
            json.dump(self.approved_projects, open(self.approved_store_path, "w", encoding="utf-8"),
                      ensure_ascii=False)

    # ====================================================
    # 处理广告邮件
    # ====================================================
    def _process_advertisement_mail(self, mail):
        print("[CompanyAgent] 收到广告，转发给主播。")

        subject = f"【广告】{mail.get('ad_title', '')}"
        content = mail.get("content", "")

        self.send_mail_to_vtuber(subject, content)

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

        project_id, project_data = next(iter(self.approved_projects.items()))

        info = self._extract_project_info(project_data)

        today = datetime.now()
        shoot_date = (today + timedelta(days=1)).date()

        def parse_dt_or_none(s, fallback_date):
            if not s:
                return None
            try:
                if len(s.strip()) <= 5 and ":" in s:  # "HH:MM"
                    hh, mm = map(int, s.strip().split(":"))
                    return datetime.combine(fallback_date, datetime.min.time()).replace(hour=hh, minute=mm)
                else:
                    # 尝试解析为完整格式
                    return datetime.strptime(s, "%Y-%m-%d %H:%M")
            except Exception:
                try:
                    return datetime.fromisoformat(s)
                except Exception:
                    return None

        preferred_start_dt = parse_dt_or_none(info["preferred_start"], shoot_date)
        preferred_end_dt = parse_dt_or_none(info["preferred_end"], shoot_date)

        # 如果只有 start 给出，end 默认 +2 小时；若都没有，则默认明天 10:00 - 12:00
        if preferred_start_dt and not preferred_end_dt:
            preferred_end_dt = preferred_start_dt + timedelta(hours=2)

        if not preferred_start_dt and not preferred_end_dt:
            start_dt = datetime.combine(shoot_date, datetime.min.time()).replace(hour=10, minute=0)
            end_dt = start_dt + timedelta(hours=2)
        else:
            start_dt = preferred_start_dt or datetime.combine(shoot_date, datetime.min.time()).replace(hour=10, minute=0)
            end_dt = preferred_end_dt or (start_dt + timedelta(hours=2))

        subject = f"【拍攝安排】企劃：{info['project_name']}"
        content = {
            "project_id": info["project_id"] or project_id,
            "project_name": info["project_name"],
            "start_time": start_dt.strftime("%Y-%m-%d %H:%M"),
            "end_time": end_dt.strftime("%Y-%m-%d %H:%M"),
            "description": info["description"] or "公司已安排拍攝，請準備相關素材。"
        }

        self.send_mail_to_vtuber(subject, content)
        print(f"[CompanyAgent] 已安排拍攝：{info['project_name']} ({content['start_time']} - {content['end_time']})")

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
