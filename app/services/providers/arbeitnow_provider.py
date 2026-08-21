import urllib.request
import json
from .base_provider import BaseProvider
import re
from datetime import datetime

class ArbeitnowProvider(BaseProvider):
    source_name = "Arbeitnow"
    source_url = "https://www.arbeitnow.com/"
    
    def fetch_internships(self):
        """Fetch jobs from Arbeitnow, trying to filter for internships/entry-level."""
        url = "https://www.arbeitnow.com/api/job-board-api"
        internships = []
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    
                    for job in data.get('data', []):
                        # Only include jobs that are likely internships or entry level
                        title = job.get('title', '').lower()
                        if 'intern' in title or 'junior' in title or 'entry' in title or 'student' in title or 'working student' in title or 'trainee' in title:
                            internships.append(job)
                            
        except Exception as e:
            print(f"Error fetching from Arbeitnow: {e}")
            
        return internships

    def normalize_internship(self, raw_data):
        """Convert Arbeitnow job format to InternBridge format."""
        
        # Strip HTML from description
        raw_desc = raw_data.get('description', '')
        desc = re.sub(r'<[^>]+>', '', raw_desc)
        
        # Tags are available for skills
        tags = raw_data.get('tags', [])
        
        work_mode = "Remote" if raw_data.get('remote') else "Hybrid" if raw_data.get('hybrid') else "On-site"
        
        # Approximate internship type
        title_lower = raw_data.get('title', '').lower()
        if 'part time' in title_lower or 'part-time' in title_lower or 'working student' in title_lower:
            internship_type = 'Part-time Internship'
        else:
            internship_type = 'Full-time Internship'
            
        # Parse created at to date if possible, else default to None for deadline
        deadline = None
        # Arbeitnow doesn't provide strict deadlines. We'll set a deadline 30 days from now to keep it active
        import datetime as dt
        deadline = (dt.datetime.utcnow() + dt.timedelta(days=30)).date()
        
        # Location normalization
        from app.utils.location_helpers import normalize_location
        raw_location = raw_data.get('location', '')
        normalized_loc = normalize_location(raw_location)
        
        return {
            'title': raw_data.get('title'),
            'company_name': raw_data.get('company_name'),
            'description': desc,
            'short_description': f"{raw_data.get('title')} at {raw_data.get('company_name')}",
            'category': 'Technology' if 'software' in desc.lower() or 'developer' in title_lower else 'General',
            'internship_type': internship_type,
            'work_mode': work_mode,
            'location': raw_location,
            'country': normalized_loc['country'],
            'state': normalized_loc['state'],
            'city': normalized_loc['city'],
            'duration': 'Flexible', # Default as it's not provided
            'application_deadline': deadline,
            'application_url': raw_data.get('url'),
            'source_name': self.source_name,
            'source_url': self.source_url,
            'external_reference_id': str(raw_data.get('slug')),
            'status': 'Published',
            'required_skills_json': tags, # Pass list, service will handle JSON encoding
            'preferred_skills_json': []
        }
