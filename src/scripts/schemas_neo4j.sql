// Legal Entity Constraints  
CREATE CONSTRAINT legal_entity_name IF NOT EXISTS FOR (e:LegalEntity) REQUIRE e.name IS UNIQUE;  
CREATE CONSTRAINT legal_provision_id IF NOT EXISTS FOR (p:LegalProvision) REQUIRE p.id IS UNIQUE;  

  
// Legal Entity Node Structure  
// (:LegalEntity {  
//   name: String,  
//   type: String, // 'legal_concept', 'legal_principle', 'legal_entity', 'legal_procedure'  
//   description: String,  
//   level: String, // 'phan', 'chuong', 'dieu', 'khoan'  
//   source_id: String,  
//   confidence_score: Float,  
//   created_at: DateTime,  
//   updated_at: DateTime  
// })  
  
// Legal Provision Node (Hierarchical Structure)  
// (:LegalProvision {  
//   id: String, // 'dieu-1', 'khoan-1-1'  
//   level: String,  
//   number: String,  
//   title: String,  
//   content: String,  
//   document_id: String,  
//   hierarchy_path: [String],  
//   cross_references: [String]  
// })  
  
// Relationship Types  
// CONTAINS - Hierarchical containment (Chương CONTAINS Điều)  
// REFERENCES - Cross-references between provisions  
// DEFINES - Entity definition relationships  
// REGULATES - Regulatory relationships  
// RELATES_TO - General semantic relationships  
// SUPERSEDES - Legal precedence relationships  
// AMENDS - Amendment relationships  
  
// Community Structure  
// (:Community {  
//   id: String,  
//   level: Integer,  
//   title: String,  
//   summary: String,  
//   entity_count: Integer,  
//   relationship_count: Integer,  
//   report_content: String  
// })  
  
// Sample Cypher Queries for Legal Domain  
// Find all entities in a specific legal provision  
MATCH (p:LegalProvision {id: 'dieu-1'})-[:DEFINES]->(e:LegalEntity)  
RETURN p, e;  
  
// Find hierarchical path for a provision  
MATCH path = (root:LegalProvision)-[:CONTAINS*]->(leaf:LegalProvision {id: 'khoan-1-1'})  
RETURN path;  
  
// Find cross-referenced provisions  
MATCH (p1:LegalProvision)-[:REFERENCES]->(p2:LegalProvision)  
WHERE p1.id = 'dieu-1'  
RETURN p1, p2;