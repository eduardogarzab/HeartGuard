@echo off
set BASE_URL=http://localhost:8000
set TOKEN=REPLACE_WITH_JWT_TOKEN

echo Listing catalog entries (JSON)...
curl -H "Authorization: Bearer %TOKEN%" ^
     -H "Accept: application/json" ^
     %BASE_URL%/v1/catalog/care_specialties

echo Listing catalog entries (XML)...
curl -H "Authorization: Bearer %TOKEN%" ^
     -H "Accept: application/xml" ^
     %BASE_URL%/v1/catalog/care_specialties

echo Creating catalog entry...
curl -X POST -H "Authorization: Bearer %TOKEN%" ^
     -H "Content-Type: application/json" ^
     -d "{\"name\":\"New Specialty\",\"description\":\"Example\"}" ^
     %BASE_URL%/v1/catalog/care_specialties

echo Updating catalog entry...
curl -X PATCH -H "Authorization: Bearer %TOKEN%" ^
     -H "Content-Type: application/json" ^
     -d "{\"description\":\"Updated description\"}" ^
     %BASE_URL%/v1/catalog/care_specialties/00000000-0000-0000-0000-000000000000

echo Deleting catalog entry...
curl -X DELETE -H "Authorization: Bearer %TOKEN%" ^
     %BASE_URL%/v1/catalog/care_specialties/00000000-0000-0000-0000-000000000000
