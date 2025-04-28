library(httr)
library(jsonlite)

url_base <- "https://api.census.gov/data/timeseries/intltrade/exports/porths?get=AIR_VAL_YR,AIR_WGT_YR,CNT_VAL_YR,CNT_WGT_YR,CTY_CODE,CTY_NAME,PORT,PORT_NAME&E_COMMODITY="
url_end <- "&YEAR&COMM_LVL=HS2&time=2024-12"



#scrape all exports for 2024

##note for some reason 77 is missing from dataset so breaks code
for (i in 1:98) {
    if (i == 77) {
        next
    }    
    i <- sprintf("%02d", i)
    url <- paste0(url_base, i, url_end)
    name <- paste0('exports_2024_', i)
    retrieve <- GET(url)
    ans <- fromJSON(content(retrieve,"text"),flatten=TRUE)
    path = paste0("Maritime_Aviation/Export_Data/",name,".csv")
    write.csv(ans,path)
}

url_base <- "https://api.census.gov/data/timeseries/intltrade/imports/porths?get=AIR_VAL_YR,AIR_WGT_YR,CNT_VAL_YR,CNT_WGT_YR,CTY_CODE,CTY_NAME,PORT,PORT_NAME&I_COMMODITY="
url_end <- "&YEAR&COMM_LVL=HS2&time=2024-12"

#scrape all imports for 2024
for (i in 1:98) {
    if (i == 77) {
        next
    }  
    i <- sprintf("%02d", i)
    url <- paste0(url_base, i, url_end)
    name <- paste0('imports_2024_', i)
    retrieve <- GET(url)
    ans <- fromJSON(content(retrieve,"text"),flatten=TRUE)
    path = paste0("Maritime_Aviation/Import_Data/",name,".csv")
    write.csv(ans,path)
}
