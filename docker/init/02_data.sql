-- Seed data for Legal Case Management (PostgreSQL)

-- Insert case record
INSERT INTO cases (case_id, case_type, date_filed, status, attorney_id, case_summary) VALUES 
(
    '2024-PI-001',
    'Personal Injury - Motor Vehicle Accident',
    '2024-03-15',
    'Active - Demand Phase',
    101,
    'Rear-end collision case where plaintiff John Smith was struck by defendant Sarah Johnson while stopped at traffic light. Clear liability with admitted fault by defendant. Plaintiff sustained soft tissue injuries to back, neck, and shoulder requiring 12 weeks of medical treatment. Total medical expenses $8,950, lost wages $4,940. Defendant was distracted by cell phone use at time of accident.'
);

-- Insert parties
INSERT INTO parties (case_id, party_type, name, contact_info, insurance_info) VALUES 
(
    '2024-PI-001',
    'plaintiff',
    'John Smith',
    '{"phone": "(555) 987-6543", "address": "456 Oak Street, Springfield, CA 90210", "email": "jsmith@email.com", "dob": "1985-06-15"}'::jsonb,
    '{"company": "State Farm", "policy": "SF-789456123", "adjuster": "Mary Johnson", "phone": "(800) 555-1234"}'::jsonb
),
(
    '2024-PI-001',
    'defendant',
    'Sarah Johnson',
    '{"phone": "(555) 456-7890", "address": "789 Pine Avenue, Springfield, CA 90215", "dob": "1992-02-22"}'::jsonb,
    '{"company": "ABC Insurance Company", "policy": "ABC-456789012", "adjuster": "Michael Rodriguez", "phone": "(800) 555-0199"}'::jsonb
),
(
    '2024-PI-001',
    'insurance_company',
    'ABC Insurance Company',
    '{"phone": "(800) 555-0199", "address": "1500 Insurance Plaza, Los Angeles, CA 90015", "claims_dept": "claims@abcinsurance.com"}'::jsonb,
    '{"limits": "100/300/50", "status": "active", "coverage_confirmed": true}'::jsonb
),
(
    '2024-PI-001',
    'witness',
    'Maria Rodriguez',
    '{"phone": "(555) 321-6547", "address": "234 Elm Street, Springfield, CA 90210"}'::jsonb,
    '{}'::jsonb
),
(
    '2024-PI-001',
    'witness',
    'Robert Chen',
    '{"phone": "(555) 654-3210", "address": "567 Maple Drive, Springfield, CA 90212"}'::jsonb,
    '{}'::jsonb
);

-- Insert documents
INSERT INTO documents (case_id, file_path, doc_category, upload_date, document_title, metadata) VALUES 
(
    '2024-PI-001',
    '/sample_docs/2024-PI-001/medical_records_dr_jones.pdf',
    'medical',
    '2024-03-20',
    'Medical Records - Dr. Michael Jones - Central Valley Medical Group',
    '{"pages": 8, "date_range": "2024-03-16 to 2024-06-10", "provider": "Dr. Michael Jones", "total_expenses": 8950, "injuries": ["lumbar strain", "cervical whiplash", "shoulder contusion"]}'::jsonb
),
(
    '2024-PI-001',
    '/sample_docs/2024-PI-001/police_report_incident_789.pdf',
    'police_report',
    '2024-03-16',
    'Police Report - SPD Report #789 - Traffic Collision',
    '{"report_number": "SPD-2024-789", "officer": "Jennifer Martinez", "fault_determination": "100% defendant", "citations": ["CVC 21703", "CVC 23123"], "total_fines": 400}'::jsonb
),
(
    '2024-PI-001',
    '/sample_docs/2024-PI-001/wage_statements_2024.pdf',
    'financial',
    '2024-07-05',
    'Wage Statements and Employment Records - Pacific Construction',
    '{"employer": "Pacific Construction Company", "position": "Construction Supervisor", "hourly_rate": 32.50, "total_wage_loss": 4940, "time_off_weeks": 10.5}'::jsonb
),
(
    '2024-PI-001',
    '/sample_docs/2024-PI-001/insurance_correspondence.pdf',
    'correspondence',
    '2024-06-25',
    'Insurance Correspondence - ABC Insurance Communications',
    '{"claim_number": "ABC-2024-789456", "adjuster": "Michael Rodriguez", "settlement_range": "25000-35000", "liability_accepted": true}'::jsonb
);

-- Insert case events
INSERT INTO case_events (case_id, event_date, event_type, description, amount) VALUES 
(
    '2024-PI-001',
    '2024-03-15',
    'accident',
    'Motor vehicle accident occurred at 15:30 hours at intersection of Main Street and First Avenue. Plaintiff rear-ended by defendant while stopped at red light. Defendant admits to cell phone distraction.',
    NULL
),
(
    '2024-PI-001',
    '2024-03-15',
    'medical_treatment',
    'Plaintiff transported by ambulance to Springfield General Hospital. Initial ER evaluation for back, neck, and shoulder injuries.',
    1200.00
),
(
    '2024-PI-001',
    '2024-03-16',
    'medical_treatment',
    'Initial examination with Dr. Michael Jones. Diagnosed with lumbar strain, cervical whiplash, and right shoulder contusion. Work restrictions imposed.',
    225.00
),
(
    '2024-PI-001',
    '2024-03-25',
    'medical_treatment',
    'MRI of lumbar spine showing mild disc bulge L4-L5. Physical therapy ordered 3x per week.',
    1400.00
),
(
    '2024-PI-001',
    '2024-03-30',
    'medical_treatment',
    'Follow-up with Dr. Jones. Persistent pain, sleep disruption. Gabapentin added for nerve pain. Work restrictions extended.',
    225.00
),
(
    '2024-PI-001',
    '2024-04-20',
    'medical_treatment',
    'Gradual improvement noted. Physical therapy reduced to 2x per week. Begin light duty work return.',
    225.00
),
(
    '2024-PI-001',
    '2024-06-10',
    'medical_treatment',
    'Final evaluation with Dr. Jones. Maximum medical improvement reached. 5% permanent partial impairment. Return to work with lifting restrictions.',
    225.00
),
(
    '2024-PI-001',
    '2024-03-16',
    'expense',
    'Ambulance transport from accident scene to Springfield General Hospital.',
    350.00
),
(
    '2024-PI-001',
    '2024-03-16',
    'expense',
    'Vehicle towing and storage fees - Jerry''s Towing Service.',
    285.00
),
(
    '2024-PI-001',
    '2024-03-20',
    'expense',
    'Prescription medications - pain medication, muscle relaxants, anti-inflammatory.',
    127.50
),
(
    '2024-PI-001',
    '2024-04-15',
    'expense',
    'Physical therapy sessions (12 sessions) - Central Valley Physical Therapy.',
    1440.00
),
(
    '2024-PI-001',
    '2024-05-20',
    'expense',
    'Additional physical therapy sessions (12 sessions) - Central Valley Physical Therapy.',
    1440.00
),
(
    '2024-PI-001',
    '2024-06-15',
    'expense',
    'Additional prescription medications and medical supplies.',
    442.50
),
(
    '2024-PI-001',
    '2024-03-16',
    'correspondence',
    'Initial claim report filed with ABC Insurance Company. Claim number ABC-2024-789456 assigned.',
    NULL
),
(
    '2024-PI-001',
    '2024-03-25',
    'correspondence',
    'Property damage settlement offer received from ABC Insurance for $12,947.83.',
    12947.83
),
(
    '2024-PI-001',
    '2024-05-20',
    'correspondence',
    'Settlement authority letter received from ABC Insurance indicating willingness to settle bodily injury claim in range of $25,000-$35,000.',
    NULL
),
(
    '2024-PI-001',
    '2024-06-25',
    'correspondence',
    'Counter-offer received from ABC Insurance for $28,500 in response to demand letter.',
    28500.00
);
