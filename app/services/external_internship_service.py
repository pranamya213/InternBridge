import json
from datetime import datetime
import logging
from app import db
from app.models.external_internship import ExternalInternship
from app.services.providers import get_all_providers

logger = logging.getLogger(__name__)

def sync_external_internships():
    """
    Synchronizes external internships from all configured providers.
    Upserts new or existing valid internships.
    Marks old/expired ones appropriately.
    """
    providers = get_all_providers()
    stats = {
        'total_fetched': 0,
        'new_added': 0,
        'updated': 0,
        'errors': 0
    }
    
    for provider in providers:
        try:
            logger.info(f"Syncing from provider: {provider.source_name}")
            raw_internships = provider.fetch_internships()
            stats['total_fetched'] += len(raw_internships)
            
            for raw_data in raw_internships:
                try:
                    normalized = provider.normalize_internship(raw_data)
                    if not normalized:
                        continue
                        
                    # Handle duplicate based on source_name + external_reference_id
                    existing = ExternalInternship.query.filter_by(
                        source_name=normalized['source_name'],
                        external_reference_id=normalized['external_reference_id']
                    ).first()
                    
                    if existing:
                        # Update fields
                        for k, v in normalized.items():
                            if k not in ['required_skills_json', 'preferred_skills_json']:
                                setattr(existing, k, v)
                                
                        # Handle JSON skills
                        if 'required_skills_json' in normalized:
                            existing.set_required_skills(normalized['required_skills_json'])
                        if 'preferred_skills_json' in normalized:
                            existing.set_preferred_skills(normalized['preferred_skills_json'])
                            
                        existing.fetched_at = datetime.utcnow()
                        stats['updated'] += 1
                    else:
                        # Insert new
                        new_internship = ExternalInternship()
                        for k, v in normalized.items():
                            if k not in ['required_skills_json', 'preferred_skills_json']:
                                setattr(new_internship, k, v)
                                
                        if 'required_skills_json' in normalized:
                            new_internship.set_required_skills(normalized['required_skills_json'])
                        if 'preferred_skills_json' in normalized:
                            new_internship.set_preferred_skills(normalized['preferred_skills_json'])
                            
                        new_internship.fetched_at = datetime.utcnow()
                        if new_internship.status == 'Published':
                            new_internship.published_at = datetime.utcnow()
                            
                        db.session.add(new_internship)
                        stats['new_added'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing normalized data for {provider.source_name}: {e}")
                    stats['errors'] += 1
                    
        except Exception as e:
            logger.error(f"Error fetching from provider {provider.source_name}: {e}")
            stats['errors'] += 1
            
    try:
        db.session.commit()
    except Exception as e:
        logger.error(f"Database commit error during sync: {e}")
        db.session.rollback()
        stats['errors'] += 1
        
    return stats
