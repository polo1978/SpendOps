-- SpendOps Mock Data v2 — Nexagen CDMO IT/OT
-- Matches actual schema from init_db.py exactly
-- FY2026 | ~$950K annual budget

-- Department
INSERT INTO departments (id, name) VALUES (1, 'IT/OT');

-- Budget cycle
INSERT INTO budget_cycles (id, name, start_date, end_date)
VALUES (1, 'FY2026', '2026-01-01', '2026-12-31');

-- Vendors
INSERT INTO vendors (id, name, website) VALUES
(1,  'Dell Technologies',     'dell.com'),
(2,  'Microsoft',             'microsoft.com'),
(3,  'Cisco Systems',         'cisco.com'),
(4,  'AWS',                   'aws.amazon.com'),
(5,  'CrowdStrike',           'crowdstrike.com'),
(6,  'Claroty',               'claroty.com'),
(7,  'Rockwell Automation',   'rockwellautomation.com'),
(8,  'Tenable',               'tenable.com'),
(9,  'ServiceNow',            'servicenow.com'),
(10, 'Veeam',                 'veeam.com'),
(11, 'SolarWinds',            'solarwinds.com'),
(12, 'ManageEngine',          'manageengine.com'),
(13, 'Siemens',               'siemens.com'),
(14, 'Zoom',                  'zoom.us'),
(15, 'Splunk',                'splunk.com'),
(16, 'IBM',                   'ibm.com'),
(17, 'Azure',                 'azure.microsoft.com'),
(18, 'Fortinet',              'fortinet.com');

-- Subscriptions
-- Demo issues baked in:
--   #3 CrowdStrike: renews in 18 days, no owner
--   #5 Claroty: renews in 9 days, auto_renew ON, no owner, $54K
--   #9 ServiceNow: owner VACANT since Jan 2026, renews Apr 10
--   #7 SolarWinds + #8 ManageEngine: overlap candidates
--   #15 IBM Maximo: VACANT owner, migration in progress, cancellable
INSERT INTO subscriptions (id, department_id, vendor_id, product_name, owner_name, renewal_date, auto_renew, annual_cost, notes) VALUES
(1,  1, 2,  'Microsoft 365 E3',              'Maria Santos',  '2026-10-15', 1, 48000.00,  '40 seats'),
(2,  1, 17, 'Azure DevOps',                  'Carlos Rivera', '2026-08-01', 1, 12000.00,  'CI/CD pipelines for MES integrations'),
(3,  1, 5,  'CrowdStrike Falcon',            NULL,            '2026-03-24', 1, 38400.00,  'OWNER NOT ASSIGNED — renewal contact unknown'),
(4,  1, 3,  'Cisco SmartNet Core Switch',    'James Okafor',  '2026-07-10', 0,  9600.00,  'Must negotiate 60 days before renewal'),
(5,  1, 6,  'Claroty xDome OT Security',     NULL,            '2026-03-15', 1, 54000.00,  'CRITICAL: renews in 9 days. No owner. Auto-renew ON. Procurement never reviewed.'),
(6,  1, 7,  'Rockwell FactoryTalk View',     'Ana Reyes',     '2026-09-20', 1, 22000.00,  'OT HMI license — SCADA lines 1 and 2'),
(7,  1, 11, 'SolarWinds NPM',                'James Okafor',  '2026-11-05', 1, 14400.00,  'IT network monitoring — possible overlap with ManageEngine'),
(8,  1, 12, 'ManageEngine OpManager',        'James Okafor',  '2026-05-18', 1,  8400.00,  'OVERLAP: covers same IT network visibility as SolarWinds'),
(9,  1, 9,  'ServiceNow ITSM',               'VACANT',        '2026-04-10', 0, 36000.00,  'Owner left Jan 2026. No renewal decision made.'),
(10, 1, 10, 'Veeam Backup & Replication',    'Carlos Rivera', '2026-12-01', 1,  9600.00,  'Covers VMs including MES and historian servers'),
(11, 1, 8,  'Tenable OT Security',           'Ana Reyes',     '2026-06-30', 0, 31200.00,  'OT vuln scanning — evaluate overlap with Claroty'),
(12, 1, 15, 'Splunk Enterprise',             'Maria Santos',  '2026-09-01', 1, 42000.00,  'SIEM — ingests OT historian + IT event logs'),
(13, 1, 13, 'Siemens SINEMA Remote Connect', 'Ana Reyes',     '2026-07-25', 1,  7200.00,  'Remote access to OT field devices'),
(14, 1, 14, 'Zoom Business',                 'Maria Santos',  '2026-10-01', 1,  4800.00,  '20 seats'),
(15, 1, 16, 'IBM Maximo (legacy)',           'VACANT',        '2026-05-01', 0, 28800.00,  'Asset mgmt — SAP migration in progress. May be cancellable.');

-- Budget lines (one per category, plus cloud lines for AWS/Azure)
-- Schema: cycle_id, department_id, category_id, vendor_id, subscription_id, description, capex_opex, is_recurring
-- category IDs from seeded data: 1=Hardware, 2=Software & Licenses, 3=Personnel, 4=Cloud & Infrastructure, 5=Security & Compliance, 6=Support & Outsourcing

-- Hardware lines
INSERT INTO budget_lines (id, cycle_id, department_id, category_id, description, capex_opex, is_recurring) VALUES
(1, 1, 1, 1, 'Laptop refresh — 15 units Dell Latitude',        'capex', 0),
(2, 1, 1, 1, 'Server hardware — OT historian + MES upgrades',  'capex', 0),
(3, 1, 1, 1, 'Networking equipment — switches and APs',        'capex', 0),
(4, 1, 1, 1, 'Mobile devices — tablets for OT floor',         'capex', 0);

-- Software & Licenses lines (linked to subscriptions)
INSERT INTO budget_lines (id, cycle_id, department_id, category_id, subscription_id, description, capex_opex, is_recurring) VALUES
(5,  1, 1, 2, 1,  'Microsoft 365 E3',             'opex', 1),
(6,  1, 1, 2, 2,  'Azure DevOps',                 'opex', 1),
(7,  1, 1, 2, 3,  'CrowdStrike Falcon',            'opex', 1),
(8,  1, 1, 2, 4,  'Cisco SmartNet',               'opex', 1),
(9,  1, 1, 2, 6,  'Rockwell FactoryTalk View',     'opex', 1),
(10, 1, 1, 2, 7,  'SolarWinds NPM',               'opex', 1),
(11, 1, 1, 2, 8,  'ManageEngine OpManager',        'opex', 1),
(12, 1, 1, 2, 9,  'ServiceNow ITSM',              'opex', 1),
(13, 1, 1, 2, 10, 'Veeam Backup',                 'opex', 1),
(14, 1, 1, 2, 13, 'Siemens SINEMA',               'opex', 1),
(15, 1, 1, 2, 14, 'Zoom Business',                'opex', 1),
(16, 1, 1, 2, 15, 'IBM Maximo (legacy)',           'opex', 1);

-- Personnel lines
INSERT INTO budget_lines (id, cycle_id, department_id, category_id, description, capex_opex, is_recurring) VALUES
(17, 1, 1, 3, 'IT/OT Manager salary + benefits',          'opex', 1),
(18, 1, 1, 3, 'OT Engineer salary + benefits',            'opex', 1),
(19, 1, 1, 3, 'IT Systems Administrator salary',          'opex', 1),
(20, 1, 1, 3, 'Help Desk Technician salary',              'opex', 1),
(21, 1, 1, 3, 'Training budget — GxP, SCADA, cloud',      'opex', 0);

-- Cloud & Infrastructure lines
INSERT INTO budget_lines (id, cycle_id, department_id, category_id, vendor_id, description, capex_opex, is_recurring) VALUES
(22, 1, 1, 4, 4,  'AWS — validation workloads + S3 backup',    'opex', 1),
(23, 1, 1, 4, 17, 'Azure — dev/test and M365 compute',         'opex', 1),
(24, 1, 1, 4, NULL,'On-premise data center — power + cooling',  'opex', 1);

-- Security & Compliance lines
INSERT INTO budget_lines (id, cycle_id, department_id, category_id, subscription_id, description, capex_opex, is_recurring) VALUES
(25, 1, 1, 5, 5,  'Claroty xDome OT Security',     'opex', 1),
(26, 1, 1, 5, 11, 'Tenable OT Security',           'opex', 1),
(27, 1, 1, 5, 12, 'Splunk Enterprise SIEM',        'opex', 1),
(28, 1, 1, 5, NULL,'Annual cybersecurity audit',    'opex', 0),
(29, 1, 1, 5, NULL,'GxP compliance assessments',   'opex', 0);

-- Support & Outsourcing lines
INSERT INTO budget_lines (id, cycle_id, department_id, category_id, description, capex_opex, is_recurring) VALUES
(30, 1, 1, 6, 'MSP — Tier 1/2 help desk coverage',        'opex', 1),
(31, 1, 1, 6, 'OT integration consultant — project-based', 'opex', 0),
(32, 1, 1, 6, 'External IT audit and pen testing',         'opex', 0);

-- Budget months
-- Hardware: server refresh hit March hard
INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(1, '2026-01', 0, 0), (1, '2026-02', 0, 0), (1, '2026-03', 0, 0),
(1, '2026-04', 22500, NULL), (1, '2026-05', 0, NULL), (1, '2026-06', 0, NULL),
(1, '2026-07', 0, NULL), (1, '2026-08', 0, NULL), (1, '2026-09', 0, NULL),
(1, '2026-10', 0, NULL), (1, '2026-11', 0, NULL), (1, '2026-12', 0, NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(2, '2026-01', 0, 0), (2, '2026-02', 0, 0), (2, '2026-03', 41500, 41500),
(2, '2026-04', 0, NULL), (2, '2026-05', 0, NULL), (2, '2026-06', 0, NULL),
(2, '2026-07', 0, NULL), (2, '2026-08', 0, NULL), (2, '2026-09', 0, NULL),
(2, '2026-10', 0, NULL), (2, '2026-11', 0, NULL), (2, '2026-12', 0, NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(3, '2026-01', 0, 0), (3, '2026-02', 0, 0), (3, '2026-03', 0, 0),
(3, '2026-04', 0, NULL), (3, '2026-05', 0, NULL), (3, '2026-06', 18000, NULL),
(3, '2026-07', 0, NULL), (3, '2026-08', 0, NULL), (3, '2026-09', 0, NULL),
(3, '2026-10', 0, NULL), (3, '2026-11', 0, NULL), (3, '2026-12', 0, NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(4, '2026-01', 0, 0), (4, '2026-02', 0, 0), (4, '2026-03', 0, 0),
(4, '2026-04', 0, NULL), (4, '2026-05', 8400, NULL), (4, '2026-06', 0, NULL),
(4, '2026-07', 0, NULL), (4, '2026-08', 0, NULL), (4, '2026-09', 0, NULL),
(4, '2026-10', 0, NULL), (4, '2026-11', 0, NULL), (4, '2026-12', 0, NULL);

-- Software subscriptions: monthly recurring amounts
INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(5,'2026-01',4000,4000),(5,'2026-02',4000,4000),(5,'2026-03',4000,4000),
(5,'2026-04',4000,NULL),(5,'2026-05',4000,NULL),(5,'2026-06',4000,NULL),
(5,'2026-07',4000,NULL),(5,'2026-08',4000,NULL),(5,'2026-09',4000,NULL),
(5,'2026-10',4000,NULL),(5,'2026-11',4000,NULL),(5,'2026-12',4000,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(6,'2026-01',1000,1000),(6,'2026-02',1000,1000),(6,'2026-03',1000,1000),
(6,'2026-04',1000,NULL),(6,'2026-05',1000,NULL),(6,'2026-06',1000,NULL),
(6,'2026-07',1000,NULL),(6,'2026-08',1000,NULL),(6,'2026-09',1000,NULL),
(6,'2026-10',1000,NULL),(6,'2026-11',1000,NULL),(6,'2026-12',1000,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(7,'2026-01',3200,3200),(7,'2026-02',3200,3200),(7,'2026-03',3200,3200),
(7,'2026-04',3200,NULL),(7,'2026-05',3200,NULL),(7,'2026-06',3200,NULL),
(7,'2026-07',3200,NULL),(7,'2026-08',3200,NULL),(7,'2026-09',3200,NULL),
(7,'2026-10',3200,NULL),(7,'2026-11',3200,NULL),(7,'2026-12',3200,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(8,'2026-01',800,800),(8,'2026-02',800,800),(8,'2026-03',800,800),
(8,'2026-04',800,NULL),(8,'2026-05',800,NULL),(8,'2026-06',800,NULL),
(8,'2026-07',800,NULL),(8,'2026-08',800,NULL),(8,'2026-09',800,NULL),
(8,'2026-10',800,NULL),(8,'2026-11',800,NULL),(8,'2026-12',800,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(9,'2026-01',1833,1833),(9,'2026-02',1833,1833),(9,'2026-03',1833,1833),
(9,'2026-04',1833,NULL),(9,'2026-05',1833,NULL),(9,'2026-06',1833,NULL),
(9,'2026-07',1833,NULL),(9,'2026-08',1833,NULL),(9,'2026-09',1833,NULL),
(9,'2026-10',1833,NULL),(9,'2026-11',1833,NULL),(9,'2026-12',1833,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(10,'2026-01',1200,1200),(10,'2026-02',1200,1200),(10,'2026-03',1200,1200),
(10,'2026-04',1200,NULL),(10,'2026-05',1200,NULL),(10,'2026-06',1200,NULL),
(10,'2026-07',1200,NULL),(10,'2026-08',1200,NULL),(10,'2026-09',1200,NULL),
(10,'2026-10',1200,NULL),(10,'2026-11',1200,NULL),(10,'2026-12',1200,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(11,'2026-01',700,700),(11,'2026-02',700,700),(11,'2026-03',700,700),
(11,'2026-04',700,NULL),(11,'2026-05',700,NULL),(11,'2026-06',700,NULL),
(11,'2026-07',700,NULL),(11,'2026-08',700,NULL),(11,'2026-09',700,NULL),
(11,'2026-10',700,NULL),(11,'2026-11',700,NULL),(11,'2026-12',700,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(12,'2026-01',3000,3000),(12,'2026-02',3000,3000),(12,'2026-03',3000,3000),
(12,'2026-04',3000,NULL),(12,'2026-05',3000,NULL),(12,'2026-06',3000,NULL),
(12,'2026-07',3000,NULL),(12,'2026-08',3000,NULL),(12,'2026-09',3000,NULL),
(12,'2026-10',3000,NULL),(12,'2026-11',3000,NULL),(12,'2026-12',3000,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(13,'2026-01',800,800),(13,'2026-02',800,800),(13,'2026-03',800,800),
(13,'2026-04',800,NULL),(13,'2026-05',800,NULL),(13,'2026-06',800,NULL),
(13,'2026-07',800,NULL),(13,'2026-08',800,NULL),(13,'2026-09',800,NULL),
(13,'2026-10',800,NULL),(13,'2026-11',800,NULL),(13,'2026-12',800,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(14,'2026-01',600,600),(14,'2026-02',600,600),(14,'2026-03',600,600),
(14,'2026-04',600,NULL),(14,'2026-05',600,NULL),(14,'2026-06',600,NULL),
(14,'2026-07',600,NULL),(14,'2026-08',600,NULL),(14,'2026-09',600,NULL),
(14,'2026-10',600,NULL),(14,'2026-11',600,NULL),(14,'2026-12',600,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(15,'2026-01',400,400),(15,'2026-02',400,400),(15,'2026-03',400,400),
(15,'2026-04',400,NULL),(15,'2026-05',400,NULL),(15,'2026-06',400,NULL),
(15,'2026-07',400,NULL),(15,'2026-08',400,NULL),(15,'2026-09',400,NULL),
(15,'2026-10',400,NULL),(15,'2026-11',400,NULL),(15,'2026-12',400,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(16,'2026-01',2400,2400),(16,'2026-02',2400,2400),(16,'2026-03',2400,2400),
(16,'2026-04',2400,NULL),(16,'2026-05',2400,NULL),(16,'2026-06',2400,NULL),
(16,'2026-07',2400,NULL),(16,'2026-08',2400,NULL),(16,'2026-09',2400,NULL),
(16,'2026-10',2400,NULL),(16,'2026-11',2400,NULL),(16,'2026-12',2400,NULL);

-- Personnel: stable, slight underspend (open headcount)
INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(17,'2026-01',6800,6200),(17,'2026-02',6800,6200),(17,'2026-03',6800,6200),
(17,'2026-04',6800,NULL),(17,'2026-05',6800,NULL),(17,'2026-06',6800,NULL),
(17,'2026-07',6800,NULL),(17,'2026-08',6800,NULL),(17,'2026-09',6800,NULL),
(17,'2026-10',6800,NULL),(17,'2026-11',6800,NULL),(17,'2026-12',6800,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(18,'2026-01',5500,5500),(18,'2026-02',5500,5500),(18,'2026-03',5500,5500),
(18,'2026-04',5500,NULL),(18,'2026-05',5500,NULL),(18,'2026-06',5500,NULL),
(18,'2026-07',5500,NULL),(18,'2026-08',5500,NULL),(18,'2026-09',5500,NULL),
(18,'2026-10',5500,NULL),(18,'2026-11',5500,NULL),(18,'2026-12',5500,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(19,'2026-01',4200,4200),(19,'2026-02',4200,4200),(19,'2026-03',4200,4200),
(19,'2026-04',4200,NULL),(19,'2026-05',4200,NULL),(19,'2026-06',4200,NULL),
(19,'2026-07',4200,NULL),(19,'2026-08',4200,NULL),(19,'2026-09',4200,NULL),
(19,'2026-10',4200,NULL),(19,'2026-11',4200,NULL),(19,'2026-12',4200,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(20,'2026-01',3100,3100),(20,'2026-02',3100,3100),(20,'2026-03',3100,0),
(20,'2026-04',3100,NULL),(20,'2026-05',3100,NULL),(20,'2026-06',3100,NULL),
(20,'2026-07',3100,NULL),(20,'2026-08',3100,NULL),(20,'2026-09',3100,NULL),
(20,'2026-10',3100,NULL),(20,'2026-11',3100,NULL),(20,'2026-12',3100,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(21,'2026-01',833,0),(21,'2026-02',833,0),(21,'2026-03',833,1200),
(21,'2026-04',833,NULL),(21,'2026-05',833,NULL),(21,'2026-06',833,NULL),
(21,'2026-07',833,NULL),(21,'2026-08',833,NULL),(21,'2026-09',833,NULL),
(21,'2026-10',833,NULL),(21,'2026-11',833,NULL),(21,'2026-12',833,NULL);

-- Cloud: AWS overspend (validation workloads spiking)
INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(22,'2026-01',5800,7200),(22,'2026-02',5800,8400),(22,'2026-03',5800,9900),
(22,'2026-04',5800,NULL),(22,'2026-05',5800,NULL),(22,'2026-06',5800,NULL),
(22,'2026-07',5800,NULL),(22,'2026-08',5800,NULL),(22,'2026-09',5800,NULL),
(22,'2026-10',5800,NULL),(22,'2026-11',5800,NULL),(22,'2026-12',5800,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(23,'2026-01',2500,2500),(23,'2026-02',2500,2500),(23,'2026-03',2500,2800),
(23,'2026-04',2500,NULL),(23,'2026-05',2500,NULL),(23,'2026-06',2500,NULL),
(23,'2026-07',2500,NULL),(23,'2026-08',2500,NULL),(23,'2026-09',2500,NULL),
(23,'2026-10',2500,NULL),(23,'2026-11',2500,NULL),(23,'2026-12',2500,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(24,'2026-01',1800,1800),(24,'2026-02',1800,1800),(24,'2026-03',1800,1800),
(24,'2026-04',1800,NULL),(24,'2026-05',1800,NULL),(24,'2026-06',1800,NULL),
(24,'2026-07',1800,NULL),(24,'2026-08',1800,NULL),(24,'2026-09',1800,NULL),
(24,'2026-10',1800,NULL),(24,'2026-11',1800,NULL),(24,'2026-12',1800,NULL);

-- Security: on track
INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(25,'2026-01',4500,4500),(25,'2026-02',4500,4500),(25,'2026-03',4500,4500),
(25,'2026-04',4500,NULL),(25,'2026-05',4500,NULL),(25,'2026-06',4500,NULL),
(25,'2026-07',4500,NULL),(25,'2026-08',4500,NULL),(25,'2026-09',4500,NULL),
(25,'2026-10',4500,NULL),(25,'2026-11',4500,NULL),(25,'2026-12',4500,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(26,'2026-01',2600,2600),(26,'2026-02',2600,2600),(26,'2026-03',2600,2600),
(26,'2026-04',2600,NULL),(26,'2026-05',2600,NULL),(26,'2026-06',2600,NULL),
(26,'2026-07',2600,NULL),(26,'2026-08',2600,NULL),(26,'2026-09',2600,NULL),
(26,'2026-10',2600,NULL),(26,'2026-11',2600,NULL),(26,'2026-12',2600,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(27,'2026-01',3500,3500),(27,'2026-02',3500,3500),(27,'2026-03',3500,3500),
(27,'2026-04',3500,NULL),(27,'2026-05',3500,NULL),(27,'2026-06',3500,NULL),
(27,'2026-07',3500,NULL),(27,'2026-08',3500,NULL),(27,'2026-09',3500,NULL),
(27,'2026-10',3500,NULL),(27,'2026-11',3500,NULL),(27,'2026-12',3500,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(28,'2026-01',0,0),(28,'2026-02',0,0),(28,'2026-03',0,0),
(28,'2026-04',0,NULL),(28,'2026-05',0,NULL),(28,'2026-06',12000,NULL),
(28,'2026-07',0,NULL),(28,'2026-08',0,NULL),(28,'2026-09',0,NULL),
(28,'2026-10',0,NULL),(28,'2026-11',0,NULL),(28,'2026-12',0,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(29,'2026-01',0,0),(29,'2026-02',0,0),(29,'2026-03',0,0),
(29,'2026-04',8000,NULL),(29,'2026-05',0,NULL),(29,'2026-06',0,NULL),
(29,'2026-07',0,NULL),(29,'2026-08',0,NULL),(29,'2026-09',8000,NULL),
(29,'2026-10',0,NULL),(29,'2026-11',0,NULL),(29,'2026-12',0,NULL);

-- Support & Outsourcing: under budget YTD
INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(30,'2026-01',2500,2200),(30,'2026-02',2500,2200),(30,'2026-03',2500,2200),
(30,'2026-04',2500,NULL),(30,'2026-05',2500,NULL),(30,'2026-06',2500,NULL),
(30,'2026-07',2500,NULL),(30,'2026-08',2500,NULL),(30,'2026-09',2500,NULL),
(30,'2026-10',2500,NULL),(30,'2026-11',2500,NULL),(30,'2026-12',2500,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(31,'2026-01',0,0),(31,'2026-02',0,0),(31,'2026-03',0,0),
(31,'2026-04',0,NULL),(31,'2026-05',0,NULL),(31,'2026-06',0,NULL),
(31,'2026-07',15000,NULL),(31,'2026-08',0,NULL),(31,'2026-09',0,NULL),
(31,'2026-10',0,NULL),(31,'2026-11',0,NULL),(31,'2026-12',0,NULL);

INSERT INTO budget_months (budget_line_id, month, planned_amount, actual_amount) VALUES
(32,'2026-01',0,0),(32,'2026-02',0,0),(32,'2026-03',0,0),
(32,'2026-04',0,NULL),(32,'2026-05',0,NULL),(32,'2026-06',0,NULL),
(32,'2026-07',0,NULL),(32,'2026-08',0,NULL),(32,'2026-09',9500,NULL),
(32,'2026-10',0,NULL),(32,'2026-11',0,NULL),(32,'2026-12',0,NULL);