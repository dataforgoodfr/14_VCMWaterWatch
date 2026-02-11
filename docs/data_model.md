## Construction

We work with:

- **Geographic areas** (countries, municipalities, etc.)
- **Actors** (distribution companies, NGOs, etc.)
- **Interactions** carried out with these actors concerning the areas

### Areas to display on the map

- Country  
- Region (not displayed on the map, but used to categorize health agencies)  
- Distribution Zone  
- Municipality (not directly displayed on the map, but used to calculate the surface of a distribution zone)

### Analysis level

Analyses are performed at the **municipality** level.

### Interactions

Interactions are carried out with respect to a **municipality**, a **country**, or a **distribution zone**.

### Templates

Templates are **country-specific**.

### Actors covering multiple distribution zones

Some actors cover multiple distribution zones:

- A water distribution company may have divided management zones (UGEs)
- A health agency operates at the regional or national level
- An elected official or an NGO may operate at the municipality, regional, or country level  
  (potentially with multiple zones, and multiple entities per zone)

### Importance of the municipality level

The **municipality** level is important because it is the most granular one; this is where we find the most specific information for the user.


## Diagram

```mermaid
erDiagram
  Country {
    string Code "2-letter ISO code"
    string Name
    geo Geometry
    enum PVCLevel "Unknown,Safe,Unsafe"
    enum Analysis "Unknown,Safe,Unsafe"
    string Tooltip
  }
  Country ||--o{ DistributionZone : "contient"
  DistributionZone {
    string Code "Code Postal, ISO code, etc"
    string Name
    geo Geometry
    enum PVCLevel "Unknown,Safe,Unsafe"
    enum Analysis "Unknown,Safe,Unsafe"
    string Tooltip
  }  
  Country ||--o{ Municipality : "contient"
  DistributionZone ||--o{ Municipality : "contient"  
  Municipality {
    string Code "Code Postal or municipality name"
    string Name
    geo Geometry
    enum PVCLevel "Unknown,Safe,Unsafe"
    enum Analysis "Unknown,Safe,Unsafe"
    string Tooltip
  }    
  
  %% Entities managing zones
  "Actor" }o--o{ DistributionZone : "gère/responsable"
  "Actor" }o--|| DistributionZone : "actif dans"  
  "Actor" {
    enum Type "ONG, Compagnie Eau, Élu"
    string Email
    string Website
    string Description
  }
  %% In case we have extra contacts
  "ContactPerson" {
    string Title
    string Name
    enum SourceOfInformation "Public Website, Political Record, ..."
    string Email
    bool DoNotContact
  }
  Actor ||--o{ ContactPerson : ""
  
  %% Interactions
  Interaction }o--|| DistributionZone : "au sujet de"
  Interaction }o--|| "Actor" : "faite avec"


  %% Interactions are how we collect information.  They can be submitted by volunteers
  %% then evaluated.
  %% Once an interaction is analyzed the data in the related ServiceArea(s) can be updated    
  Interaction {
    enum Type "Email|Phone|Other"
    enum Status "Envoyé|Reçu|Responded|Analyzed|Rejected"
    string CollectedBy "Name of the person who submitted the info"
    enum Subject "Request for Information|Informing of Risk|Other"      
    date SendDate
    date AcknowledgementDate
    date ResponseDate
    date AnalysisDate
    string ResponseContent "Raw response content"
    string PVCNotes
    string CVMNotes
  }
  Interaction ||--o{ Attachment : ""
    
  Template |o--|| Country : "pour pays"
  Template {
    enum DestinationType "Health Agency|Water Distributor|Elected Official|NGO"
    string Content
  }

  %% Analyses
  Analysis }o--|| DistributionZone : "faite dans"
  Analysis }o--|| Municipality : "faite dans"  
  Analysis {
    date Date
    string Description
    float CVMMeasure "mcg/l"
  }

```
