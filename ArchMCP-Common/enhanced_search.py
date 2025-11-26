#!/usr/bin/env python3
"""
Enhanced Search Module
Uses LLM-generated keyword mappings for improved search and matching
"""

import json
from pathlib import Path

class EnhancedSearch:
    def __init__(self):
        self.keywords_mapping = {}
        self.search_cache = {}  # Cache for search results
        self.load_keywords_mapping()
    
    def load_keywords_mapping(self):
        """Load the LLM-generated keywords mapping"""
        try:
            # Try multiple paths to find the keywords mapping file
            possible_paths = [
                Path('config/keywords_mapping.json'),
                Path('keywords_mapping.json'),
                Path('../config/keywords_mapping.json'),
                Path('../../config/keywords_mapping.json'),
                Path(__file__).parent / 'keywords_mapping.json',
                Path(__file__).parent.parent / 'inputs' / 'keywords_mapping.json',
                Path(__file__).parent.parent / 'ArchMCP-Ppt' / 'config' / 'keywords_mapping.json'
            ]
            
            keywords_file = None
            for path in possible_paths:
                if path.exists():
                    keywords_file = path
                    break
            
            if keywords_file:
                with open(keywords_file, 'r') as f:
                    self.keywords_mapping = json.load(f)
                print(f"✅ Loaded keywords for {len(self.keywords_mapping)} icons from {keywords_file.name}")
            else:
                print("⚠️ Keywords mapping not found. Run generate_keywords.py first.")
        except Exception as e:
            print(f"❌ Error loading keywords mapping: {e}")
    
    def normalize_search_term(self, term):
        """Convert search term to both singular and plural forms for better matching"""
        term = term.lower().strip()
        variations = [term]  # Always include original
        
        # Generate singular form if term appears plural
        if term.endswith('ies'):
            variations.append(term[:-3] + 'y')  # "policies" -> "policy"
        elif term.endswith('es') and len(term) > 3:
            variations.append(term[:-2])  # "boxes" -> "box"
        elif term.endswith('s') and len(term) > 2:
            variations.append(term[:-1])  # "regions" -> "region"
        
        # Generate plural form if term appears singular
        if term.endswith('y') and len(term) > 2:
            variations.append(term[:-1] + 'ies')  # "policy" -> "policies"
        elif term.endswith(('s', 'sh', 'ch', 'x', 'z')):
            variations.append(term + 'es')  # "box" -> "boxes"
        elif not term.endswith('s'):
            variations.append(term + 's')  # "region" -> "regions"
        
        return list(set(variations))  # Remove duplicates
    
    def search_icons(self, search_term, all_icons, use_keywords=True):
        """Enhanced search using keyword mappings with caching"""
        if not search_term:
            return all_icons
        
        # Create cache key from search term and icon count
        cache_key = f"{search_term.lower()}_{len(all_icons)}_{use_keywords}"
        
        # Check cache first
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        # Normalize search term to handle singular/plural variations
        search_variations = self.normalize_search_term(search_term)
        print(f"🔍 Search variations for '{search_term}': {search_variations}")
        
        results = []
        
        # Score-based ranking system
        scored_results = []
        
        for icon in all_icons:
            score = 0
            icon_name = icon['name']
            
            # Check if we have keyword mapping for this icon
            if use_keywords and icon_name in self.keywords_mapping:
                mapping = self.keywords_mapping[icon_name]
                
                # Try all search variations and take the best score
                best_score = 0
                for search_var in search_variations:
                    var_score = 0
                    
                    # Exact match in aliases (highest score)
                    aliases = mapping.get('aliases', [])
                    for alias in aliases:
                        if search_var == alias.lower():
                            var_score += 100
                        elif search_var in alias.lower():
                            var_score += 50
                    
                    # Match in keywords
                    keywords = mapping.get('keywords', [])
                    for keyword in keywords:
                        if search_var == keyword.lower():
                            var_score += 80
                        elif search_var in keyword.lower():
                            var_score += 30
                    
                    # Match in common phrases
                    phrases = mapping.get('common_phrases', [])
                    for phrase in phrases:
                        if search_var == phrase.lower():
                            var_score += 70
                        elif search_var in phrase.lower():
                            var_score += 25
                    
                    # Match in abbreviations
                    abbreviations = mapping.get('abbreviations', [])
                    for abbr in abbreviations:
                        if search_var == abbr.lower():
                            var_score += 90
                        elif search_var in abbr.lower():
                            var_score += 40
                    
                    # Match in categories
                    categories = mapping.get('categories', [])
                    for category in categories:
                        if search_var in category.lower():
                            var_score += 20
                    
                    best_score = max(best_score, var_score)
                
                score = best_score
            
            # Fallback: traditional name and category matching with variations
            if score == 0:
                fallback_score = 0
                for search_var in search_variations:
                    if search_var in icon_name.lower():
                        fallback_score = max(fallback_score, 70)
                    if search_var in icon['category'].lower():
                        fallback_score = max(fallback_score, 30)
                score = fallback_score
            
            if score > 0:
                scored_results.append((icon, score))
        
        # Sort by score (highest first) and return icons
        scored_results.sort(key=lambda x: x[1], reverse=True)
        result_icons = [icon for icon, score in scored_results]
        
        # Cache the result
        self.search_cache[cache_key] = result_icons
        
        # Limit cache size to prevent memory issues
        if len(self.search_cache) > 100:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self.search_cache))
            del self.search_cache[oldest_key]
        
        return result_icons
    
    def find_service_matches(self, service_name, icons_catalog):
        """Enhanced service matching for LLM analysis"""
        matches = []
        
        # Remove quantity prefixes: "2 EC2 instances" -> "EC2 instances"
        import re
        cleaned_service = re.sub(r'^\d+\s+', '', service_name).strip()
        cleaned_lower = cleaned_service.lower()
        
        # Check for exact icon name match first (with or without .png)
        exact_match_names = [
            cleaned_service,
            cleaned_service + '.png',
            cleaned_service.replace('.png', '') + '.png'
        ]
        
        for exact_name in exact_match_names:
            if exact_name in self.keywords_mapping:
                print(f"✅ Exact icon name match: '{service_name}' -> '{exact_name}'")
                return [{
                    'name': exact_name,
                    'page': self.keywords_mapping[exact_name].get('page', 0),
                    'category': self.keywords_mapping[exact_name].get('category', ''),
                    'path': self.keywords_mapping[exact_name].get('path', ''),
                    'score': 1000
                }]
        
        # Use pluralization normalization for better matching
        search_variations = self.normalize_search_term(cleaned_service)
        print(f"🔍 Enhanced matching for: '{service_name}' -> '{cleaned_service}' -> variations: {search_variations}")
        
        # Group-specific mappings for better matching (include both singular and plural)
        group_mappings = {
            'vpc container': 'Group_VirtualPrivateCloud',
            'vpc': 'Group_VirtualPrivateCloud', 
            'vpcs': 'Group_VirtualPrivateCloud',
            'private subnet': 'Group_Privatesubnet',
            'private subnets': 'Group_Privatesubnet',
            'public subnet': 'Group_PublicSubnet', 
            'public subnets': 'Group_PublicSubnet',
            'aws cloud': 'Group_AWSCloud_1',
            'availability zone': 'Group_AvailabilityZone',
            'availability zones': 'Group_AvailabilityZone',
            'region': 'Group_Region',
            'regions': 'Group_Region',
            'security group': 'Group_Securitygroup',
            'security groups': 'Group_Securitygroup',
            'auto scaling group': 'Group_AutoScalingGroup',
            'auto scaling groups': 'Group_AutoScalingGroup'
        }
        
        # Service-specific mappings for better matching
        service_mappings = {
            'instance': 'Amazon_Elastic_Compute_Cloud_Amazon_EC2',  # Default instance = EC2
            'instances': 'Amazon_Elastic_Compute_Cloud_Amazon_EC2',
            'ec2 instance': 'Amazon_Elastic_Compute_Cloud_Amazon_EC2',
            'ec2 instances': 'Amazon_Elastic_Compute_Cloud_Amazon_EC2',
            'application load balancer': 'Application_Load_Balancer',
            'application load balancers': 'Application_Load_Balancer',
            'internet gateway': 'Internet_gateway',
            'internet gateways': 'Internet_gateway'
        }
        
        # Check for direct group mapping first (try all variations)
        for search_var in search_variations:
            for group_term, group_icon in group_mappings.items():
                if group_term == search_var:
                    if group_icon in self.keywords_mapping:
                        matches.append({
                            'name': group_icon,
                            'path': self.keywords_mapping[group_icon]['path'],
                            'category': self.keywords_mapping[group_icon]['category'],
                            'score': 1000  # High score for direct group matches
                        })
        
        # Check for direct service mapping (try all variations)
        for search_var in search_variations:
            for service_term, service_icon in service_mappings.items():
                if service_term == search_var:
                    if service_icon in self.keywords_mapping:
                        matches.append({
                            'name': service_icon,
                            'path': self.keywords_mapping[service_icon]['path'],
                            'category': self.keywords_mapping[service_icon]['category'],
                            'score': 1000  # High score for direct service matches
                        })
                    print(f"✅ Direct service match: '{cleaned_service}' -> '{service_icon}'")
                    matches.sort(key=lambda x: x['score'], reverse=True)
                    return matches[:3]
        
        # Check for direct group mapping first
        for group_term, group_icon in group_mappings.items():
            if group_term in cleaned_lower:
                if group_icon in self.keywords_mapping:
                    matches.append({
                        'name': group_icon,
                        'path': self.keywords_mapping[group_icon]['path'],
                        'category': self.keywords_mapping[group_icon]['category'],
                        'score': 1000  # High score for direct group matches
                    })
                    print(f"✅ Direct group match: '{cleaned_service}' -> '{group_icon}'")
                    matches.sort(key=lambda x: x['score'], reverse=True)
                    return matches[:3]
        
        # Search through keyword mappings
        for icon_name, mapping in self.keywords_mapping.items():
            score = 0
            
            # Try all search variations
            for search_var in search_variations:
                var_score = 0
                
                # Check aliases (highest priority)
                aliases = mapping.get('aliases', [])
                for alias in aliases:
                    if search_var == alias.lower():
                        var_score = max(var_score, 100)
                    elif len(search_var) > 3 and (search_var in alias.lower() or alias.lower() in search_var):
                        var_score = max(var_score, 70)
                
                # Check keywords
                keywords = mapping.get('keywords', [])
                for keyword in keywords:
                    if search_var == keyword.lower():
                        var_score = max(var_score, 100)
                    elif len(search_var) > 3 and (search_var in keyword.lower() or keyword.lower() in search_var):
                        var_score = max(var_score, 50)
                
                # Check common phrases
                phrases = mapping.get('common_phrases', [])
                for phrase in phrases:
                    if search_var in phrase.lower() or phrase.lower() in search_var:
                        var_score = max(var_score, 60)
                
                # Check abbreviations
                abbreviations = mapping.get('abbreviations', [])
                for abbr in abbreviations:
                    if search_var == abbr.lower():
                        var_score = max(var_score, 90)
                    elif abbr.lower() in search_var or search_var in abbr.lower():
                        var_score = max(var_score, 60)
                
                score = max(score, var_score)
            
            # Apply category-based scoring adjustments
            category = mapping.get('category', '')
            is_group_icon = icon_name.startswith('Group_')
            is_service_query = not any(group_term in cleaned_lower for group_term in group_mappings.keys())
            
            # Prefer service icons for service queries, group icons for group queries
            if is_service_query and is_group_icon:
                score = score * 0.5  # Reduce score for group icons when querying services
            elif not is_service_query and not is_group_icon:
                score = score * 0.7  # Slightly reduce score for service icons when querying groups
            
            if score >= 50:  # Minimum threshold for matches
                matches.append({
                    'name': icon_name,
                    'page': mapping.get('page', 0),
                    'category': mapping.get('category', ''),
                    'path': mapping.get('path', ''),
                    'score': score
                })
        
        # Sort by score and return top matches
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        if matches:
            print(f"✅ Found {len(matches)} matches, top match: {matches[0]['name']} (score: {matches[0]['score']})")
            
            # Check for ambiguous matches (multiple high-scoring options)
            if len(matches) >= 2:
                top_score = matches[0]['score']
                second_score = matches[1]['score']
                score_diff_percent = (top_score - second_score) / top_score * 100
                
                # If top matches are within 15% of each other, mark as ambiguous
                if score_diff_percent <= 15:
                    matches[0]['ambiguous'] = True
                    matches[0]['alternatives'] = matches[1:4]  # Include up to 3 alternatives
                    print(f"⚠️ Ambiguous match detected - top scores within 15%: {top_score} vs {second_score}")
        else:
            print(f"❌ No enhanced matches found for '{service_name}'")
        
        return matches  # Return all matches

def test_enhanced_search():
    """Test the enhanced search functionality"""
    search = EnhancedSearch()
    
    # Test cases
    test_queries = [
        "ec2",
        "load balancer", 
        "nat gateway",
        "2 instances",
        "database",
        "storage",
        "lambda function"
    ]
    
    print("🧪 Testing Enhanced Search")
    print("=" * 30)
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        matches = search.find_service_matches(query, {})
        for match in matches[:3]:
            print(f"  → {match['name']} (score: {match['score']})")

if __name__ == "__main__":
    test_enhanced_search()
