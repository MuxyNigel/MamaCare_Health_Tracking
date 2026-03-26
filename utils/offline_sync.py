# utils/offline_sync.py
import sqlite3
import requests
import json
from datetime import datetime
import pandas as pd

class OfflineSync:
    def __init__(self, local_db_path, remote_url, api_key):
        self.local_db_path = local_db_path
        self.remote_url = remote_url
        self.api_key = api_key
    
    def sync_to_cloud(self):
        """Sync local changes to cloud database"""
        try:
            # Get local changes (new records since last sync)
            conn = sqlite3.connect(self.local_db_path)
            
            # Get mothers that need sync
            mothers = pd.read_sql("""
                SELECT * FROM mothers 
                WHERE created_at > (SELECT COALESCE(MAX(sync_time), '1970-01-01') FROM sync_log WHERE table_name = 'mothers')
            """, conn)
            
            # Send to remote (simulated)
            for _, mother in mothers.iterrows():
                payload = mother.to_dict()
                # response = requests.post(f"{self.remote_url}/api/mothers", 
                #                         json=payload, 
                #                         headers={"Authorization": f"Bearer {self.api_key}"})
                
                # Log sync
                conn.execute("""
                    INSERT INTO sync_log (table_name, record_id, sync_time, status)
                    VALUES (?, ?, ?, ?)
                """, ("mothers", mother['id'], datetime.now(), "success"))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "records_synced": len(mothers)}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def pull_from_cloud(self):
        """Pull latest data from cloud database"""
        try:
            # response = requests.get(f"{self.remote_url}/api/mothers", 
            #                        headers={"Authorization": f"Bearer {self.api_key}"})
            # cloud_data = response.json()
            
            # For demo, we'll simulate
            cloud_data = []
            
            # Update local database
            conn = sqlite3.connect(self.local_db_path)
            for record in cloud_data:
                conn.execute("""
                    INSERT OR REPLACE INTO mothers (id, name, age, phone, village, lmp, edd, risk_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (record['id'], record['name'], record['age'], record['phone'], 
                      record['village'], record['lmp'], record['edd'], record['risk_score']))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "records_pulled": len(cloud_data)}
        
        except Exception as e:
            return {"success": False, "error": str(e)}

# Initialize sync
offline_sync = OfflineSync('maternalcare.db', 'https://your-supabase-url.supabase.co', 'your-api-key')