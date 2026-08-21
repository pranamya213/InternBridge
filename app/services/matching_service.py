import re

def normalize_skill(skill):
    if not skill:
        return ""
    # Lowercase and trim
    skill = skill.lower().strip()
    
    # Common variations mapping
    variations = {
        'react.js': 'react',
        'react js': 'react',
        'reactjs': 'react',
        'node.js': 'node',
        'nodejs': 'node',
        'node js': 'node',
        'vue.js': 'vue',
        'vuejs': 'vue',
        'vue js': 'vue',
        'angular.js': 'angular',
        'angularjs': 'angular',
        'next.js': 'nextjs',
        'next js': 'nextjs'
    }
    
    if skill in variations:
        return variations[skill]
    
    # General cleanup: remove trailing '.js' if present
    if skill.endswith('.js'):
        skill = skill[:-3]
    return skill

def match_skills(required_skills, student_skills):
    # Normalized student skills for fast lookup
    norm_student_skills = {normalize_skill(s.skill_name): s for s in student_skills}
    norm_student_skill_names = set(norm_student_skills.keys())
    
    matched = []
    missing = []
    
    for req in required_skills:
        norm_req = normalize_skill(req)
        if norm_req in norm_student_skill_names:
            matched.append(req)
        else:
            missing.append(req)
            
    return matched, missing

def get_match_category(score):
    if score >= 80:
        return "Excellent Match"
    elif score >= 65:
        return "Strong Match"
    elif score >= 50:
        return "Moderate Match"
    elif score >= 30:
        return "Low Match"
    else:
        return "Weak Match"

def calculate_match(student_profile, internship):
    """
    Calculates the match score between a student profile and an internship.
    Returns a dictionary with detailed breakdown and explanations.
    """
    # Max scores per category (Fixed 100% total)
    WEIGHTS = {
        'required_skills': 45,
        'preferred_skills': 15,
        'career_interests': 15,
        'work_mode': 10,
        'location': 5,
        'eligibility': 10
    }
    
    score = 0
    strengths = []
    improvements = []
    explanation = []
    
    # 1. Required Skills (45%)
    req_skills = internship.get_required_skills()
    student_skills_list = student_profile.skills if student_profile else []
    
    req_matched = []
    req_missing = []
    if req_skills:
        req_matched, req_missing = match_skills(req_skills, student_skills_list)
        req_pct = len(req_matched) / len(req_skills)
        score += req_pct * WEIGHTS['required_skills']
        
        if len(req_missing) == 0:
            strengths.append("You have all the required skills for this role.")
            explanation.append("Excellent! You currently have all the required skills listed for this internship.")
        elif len(req_missing) == 1:
            improvements.append(f"Improve your knowledge of {req_missing[0]}.")
            explanation.append(f"You're close to a strong match. Consider improving {req_missing[0]} to strengthen your profile for this internship.")
        else:
            missing_str = ", ".join(req_missing[:2]) + (" and others" if len(req_missing) > 2 else "")
            improvements.append(f"Learn missing required skills like {missing_str}.")
            explanation.append(f"This internship requires several skills that aren't currently listed in your profile. Consider building projects using {missing_str}.")
    else:
        # If no required skills, give full points for this section
        score += WEIGHTS['required_skills']

    # 2. Preferred Skills (15%)
    pref_skills = internship.get_preferred_skills()
    pref_matched = []
    pref_missing = []
    if pref_skills:
        pref_matched, pref_missing = match_skills(pref_skills, student_skills_list)
        pref_pct = len(pref_matched) / len(pref_skills)
        score += pref_pct * WEIGHTS['preferred_skills']
        
        if len(pref_missing) > 0:
            improvements.append(f"Adding {pref_missing[0]} could make your profile even stronger.")
            if len(req_missing) == 0:
                explanation.append(f"You meet the core requirements. Adding {pref_missing[0]} to your skill set could make your profile even stronger.")
        elif len(pref_matched) > 0:
            strengths.append("You possess preferred skills for this role.")
    else:
        score += WEIGHTS['preferred_skills']
        
    # 3. Career Interests (15%)
    career_interests = [ci.role_name.lower().strip() for ci in student_profile.career_interests] if student_profile else []
    internship_title = internship.title.lower().strip()
    internship_cat = internship.category.lower().strip() if internship.category else ""
    
    career_match = False
    for ci in career_interests:
        if ci in internship_title or ci in internship_cat or internship_cat in ci:
            career_match = True
            break
            
    if career_match:
        score += WEIGHTS['career_interests']
        strengths.append("Your career interests align with this role.")
        explanation.append("Your career interest aligns with this internship.")
    else:
        # Give partial points if they have interests listed but no exact match
        if career_interests:
            score += (WEIGHTS['career_interests'] * 0.3)
            
    # 4. Work Mode (10%)
    student_modes = student_profile.get_work_modes() if student_profile else []
    int_mode = internship.work_mode
    work_mode_match = "Neutral"
    
    if int_mode and student_modes:
        if int_mode in student_modes:
            score += WEIGHTS['work_mode']
            work_mode_match = "Match"
            strengths.append(f"The {int_mode} work mode matches your preference.")
        else:
            score += (WEIGHTS['work_mode'] * 0.2) # small negative contribution, but not zero
            work_mode_match = "Mismatch"
    else:
        # Neutral if no preference
        score += (WEIGHTS['work_mode'] * 0.5)
        
    # 5. Location (5%)
    student_locations = student_profile.get_locations() if student_profile else []
    int_loc = internship.location
    int_country = getattr(internship, 'country', None)
    int_state = getattr(internship, 'state', None)
    
    # Simple heuristic to extract student state/country from their JSON preferences
    # e.g., if they selected "Bengaluru, Karnataka, India"
    student_states = []
    student_countries = []
    
    # Let's map any obvious ones
    for sl in student_locations:
        sl_lower = sl.lower()
        if 'karnataka' in sl_lower or 'bengaluru' in sl_lower or 'bangalore' in sl_lower:
            student_states.append('Karnataka')
            student_countries.append('India')
        if 'india' in sl_lower:
            student_countries.append('India')
            
    location_match = "Neutral"
    
    if int_mode == "Remote" and "Remote" in student_locations:
        score += WEIGHTS['location']
        location_match = "Match (Remote)"
    elif int_loc and student_locations:
        # Check explicit exact match first
        if int_loc in student_locations:
            score += WEIGHTS['location'] # 5/5
            location_match = "Strong Match"
        else:
            # Intelligent fallback
            loc_matched = False
            for sl in student_locations:
                if sl.lower() in int_loc.lower() or int_loc.lower() in sl.lower():
                    score += WEIGHTS['location'] # 5/5
                    location_match = "Strong Match"
                    loc_matched = True
                    break
            
            if not loc_matched:
                if int_state and int_state in student_states:
                    score += (WEIGHTS['location'] * 0.8) # 4/5
                    location_match = "State Match"
                elif int_country and int_country in student_countries:
                    if int_country == 'India':
                        score += (WEIGHTS['location'] * 0.6) # 3/5
                        location_match = "Country Match"
                    else:
                        score += (WEIGHTS['location'] * 0.2) # 1/5
                        location_match = "Weak Match"
                elif not int_country and not int_state:
                    # Unknown
                    score += (WEIGHTS['location'] * 0.4) # 2/5
                    location_match = "Unknown"
                else:
                    # Known mismatch
                    score += 0 # 0/5
                    location_match = "Mismatch"
    else:
        score += (WEIGHTS['location'] * 0.5)

    # 6. Eligibility (10%)
    # For now, without complex unstructured parsing, if they have an active degree we give some points
    eligibility_status = "Not enough information"
    if student_profile and student_profile.education:
        score += WEIGHTS['eligibility']
        eligibility_status = "Likely Eligible"
    else:
        score += (WEIGHTS['eligibility'] * 0.5)
        
    total_score = int(round(score))
    
    return {
        'score': total_score,
        'category': get_match_category(total_score),
        'required_skills': {
            'matched': req_matched,
            'missing': req_missing,
            'percentage': int((len(req_matched)/len(req_skills)*100)) if req_skills else 100
        },
        'preferred_skills': {
            'matched': pref_matched,
            'missing': pref_missing
        },
        'career_interest_match': career_match,
        'work_mode_match': work_mode_match,
        'location_match': location_match,
        'eligibility': {
            'status': eligibility_status
        },
        'strengths': strengths,
        'improvements': improvements,
        'explanation': explanation
    }

def rank_candidates_for_internship(internship, applications, sort_by='best_match'):
    """
    Ranks applications for a given internship using the existing matching logic.
    Returns a list of applications augmented with `match_data` and sorted by the requested criteria.
    """
    for app in applications:
        # Calculate the match for each application's student profile
        app.match_data = calculate_match(app.student, internship)
        app.match_score = app.match_data['score']
        
        # Calculate profile completion percentage for tie-breaking
        profile = app.student
        fields = [
            profile.headline, profile.phone, profile.location, profile.about_me,
            profile.education, profile.skills, profile.career_interests, 
            profile.projects, profile.certifications, profile.experience, profile.professional_links
        ]
        completed_fields = sum(1 for field in fields if field)
        app.profile_completion = int((completed_fields / len(fields)) * 100) if fields else 0

    # Sorting
    if sort_by == 'best_match':
        # 1. Match score (descending), 2. Profile completion (descending), 3. Application date (ascending/earliest)
        applications.sort(key=lambda x: (x.match_score, x.profile_completion, -x.applied_at.timestamp()), reverse=True)
    elif sort_by == 'application_date':
        applications.sort(key=lambda x: x.applied_at, reverse=True)
    elif sort_by == 'profile_completion':
        applications.sort(key=lambda x: x.profile_completion, reverse=True)
        
    return applications
