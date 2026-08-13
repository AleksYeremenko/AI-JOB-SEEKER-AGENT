import json
import os
from datetime import datetime
import webbrowser

DB_FILE = "Data/database.json"
DASHBOARD_FILE = "dashboard.html"

class DBManager:
    def __init__(self):
        os.makedirs("Data", exist_ok=True)
        if not os.path.exists(DB_FILE):
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
    
    def _read_db(self):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def _write_db(self, data):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.export_dashboard()

    def add_job(self, title, company, link, source):
        data = self._read_db()
        for j in data:
            if j['link'] == link:
                return
        
        data.insert(0, {
            "title": title,
            "company": company,
            "link": link,
            "source": source,
            "status": "Seen",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "email_confirmed": False
        })
        self._write_db(data)

    def update_job_status(self, link, status, notes=""):
        data = self._read_db()
        for j in data:
            if j['link'] == link:
                j['status'] = status
                j['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if notes:
                    j['notes'] = notes
                break
        self._write_db(data)
        
    def set_email_confirmed(self, company_name):
        data = self._read_db()
        updated = False
        for j in data:
            if j['company'].lower() == company_name.lower():
                j['email_confirmed'] = True
                updated = True
        if updated:
            self._write_db(data)

    def get_job_status(self, link):
        data = self._read_db()
        for j in data:
            if j['link'] == link:
                return j.get('status', 'Seen')
        return None

    def clear_rejected_jobs(self):
        data = self._read_db()
        # Убираем все отклонённые вакансии, чтобы при смене настроек их можно было перепроверить
        filtered_data = [j for j in data if j.get('status') != 'Rejected']
        self._write_db(filtered_data)

    def clear_seen_jobs(self):
        data = self._read_db()
        filtered_data = [j for j in data if j.get('status') != 'Seen']
        self._write_db(filtered_data)

    def export_dashboard(self):
        data = self._read_db()
        json_str = json.dumps(data)
        
        interviews_count = 0
        interviews_html = ""
        try:
            if os.path.exists("Data/interview_stats.json"):
                with open("Data/interview_stats.json", "r", encoding="utf-8") as f:
                    istats = json.load(f)
                    invites = istats.get("invites", [])
                    interviews_count = len(invites)
                    if interviews_count > 0:
                        rows = ""
                        for inv in invites:
                            rows += f'''
                            <tr class="bg-purple-900/20 text-purple-200 hover:bg-purple-800/30 transition-colors">
                                <td class="p-4 text-sm">{inv.get("date", "")}</td>
                                <td class="p-4 font-semibold">{inv.get("sender", "")}</td>
                                <td class="p-4">{inv.get("subject", "")}</td>
                            </tr>'''
                        interviews_html = f'''
                        <div class="glass rounded-2xl overflow-hidden shadow-2xl mb-10 border border-purple-500/30">
                            <h2 class="text-xl font-bold p-4 bg-purple-500/20 text-purple-300">🎉 Interview Invites Found in Email</h2>
                            <table class="w-full text-left border-collapse">
                                <thead>
                                    <tr class="bg-slate-800/50 text-slate-300 text-sm uppercase tracking-wider">
                                        <th class="p-4 font-semibold">Date</th>
                                        <th class="p-4 font-semibold">Sender</th>
                                        <th class="p-4 font-semibold">Subject</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-700/50">
                                    {rows}
                                </tbody>
                            </table>
                        </div>
                        '''
        except:
            pass
            
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Job Seeker Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
        }}
        .glass {{
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
    </style>
</head>
<body class="min-h-screen p-8">
    <div class="max-w-7xl mx-auto">
        <header class="mb-10 flex justify-between items-center">
            <div>
                <h1 class="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                    Job Seeker Database
                </h1>
                <p class="text-slate-400 mt-2">Track your applications and agent progress in real-time.</p>
            </div>
            <div class="glass px-6 py-3 rounded-full flex space-x-6">
                <div class="text-center">
                    <p class="text-xs text-slate-400 uppercase tracking-wider">Total Seen</p>
                    <p class="text-xl font-bold text-blue-400" id="total-seen">0</p>
                </div>
                <div class="text-center">
                    <p class="text-xs text-slate-400 uppercase tracking-wider">Applied</p>
                    <p class="text-xl font-bold text-green-400" id="total-applied">0</p>
                </div>
                <div class="text-center">
                    <p class="text-xs text-slate-400 uppercase tracking-wider">Interviews</p>
                    <p class="text-xl font-bold text-purple-400" id="total-interviews">{interviews_count}</p>
                </div>
            </div>
        </header>

        {interviews_html}

        <div class="glass rounded-2xl overflow-hidden shadow-2xl">
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-slate-800/50 text-slate-300 text-sm uppercase tracking-wider">
                            <th class="p-4 font-semibold">Date</th>
                            <th class="p-4 font-semibold">Company</th>
                            <th class="p-4 font-semibold">Role</th>
                            <th class="p-4 font-semibold">Status</th>
                            <th class="p-4 font-semibold">Reason / Notes</th>
                            <th class="p-4 font-semibold">Link</th>
                        </tr>
                    </thead>
                    <tbody id="table-body" class="divide-y divide-slate-700/50">
                        <!-- Rows -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        const jobs = {json_str};
        const tbody = document.getElementById('table-body');
        
        let appliedCount = 0;
        
        jobs.forEach(job => {{
            if (job.status === 'Applied' || job.status === 'Success') appliedCount++;
            
            const tr = document.createElement('tr');
            tr.className = "hover:bg-slate-800/30 transition-colors duration-150";
            
            const statusColor = job.status === 'Applied' || job.status === 'Success' ? 'text-green-400 bg-green-400/10' : 
                               (job.status === 'Manual Apply Required' ? 'text-purple-400 bg-purple-400/10' : 
                               (job.status === 'Failed' ? 'text-red-400 bg-red-400/10' : 'text-yellow-400 bg-yellow-400/10'));
                               
            const notesText = job.notes ? job.notes : (job.email_confirmed ? 'Email Confirmed ✅' : '');
            
            tr.innerHTML = `
                <td class="p-4 text-sm text-slate-400">${{job.date.split(' ')[0]}}</td>
                <td class="p-4 font-semibold">${{job.company}}</td>
                <td class="p-4 text-slate-300">${{job.title}}</td>
                <td class="p-4"><span class="px-3 py-1 rounded-full text-xs font-semibold border border-transparent ${{statusColor}}">${{job.status}}</span></td>
                <td class="p-4 text-sm text-red-300">${{notesText}}</td>
                <td class="p-4"><a href="${{job.link}}" target="_blank" class="text-blue-400 hover:text-blue-300 underline text-sm">View Job</a></td>
            `;
            tbody.appendChild(tr);
        }});
        
        document.getElementById('total-seen').innerText = jobs.length;
        document.getElementById('total-applied').innerText = appliedCount;
    </script>
</body>
</html>"""
        with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
            f.write(html)

    def open_dashboard(self):
        if not os.path.exists(DASHBOARD_FILE):
            self.export_dashboard()
        webbrowser.open("file://" + os.path.abspath(DASHBOARD_FILE))

db = DBManager()
