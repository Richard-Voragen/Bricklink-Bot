from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import time

options = Options()

options.add_experimental_option('excludeSwitches', ['enable-logging'])
browser = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options) # Get local session of Chrome

def CheckCombine(num1, num2, length):
    binary1 = bin(num1).replace("0b", "")
    while (len(binary1) < length):
        binary1 = "0" + binary1
    binary2 = bin(num2).replace("0b", "")
    while (len(binary2) < length):
        binary2 = "0" + binary2
    for i in range(length):
        if binary1[i] == "1" and binary2[i] == "1":
            return bool(False)
    return bool(True)


def recurse_call(graph, index, combos):
    for value in graph[index]:
        combo = []
        if (value + index == (len(graph)*2)-1):
            combo.append(value)
            combo.append(index)
            combos.append(combo)
            break
        elif (value + index > len(graph)):
            continue
        combo = recurse(graph, value+index)
        combo.append(value)
        combo.append(index)
        combos.append(combo)
    #return combos

def recurse(graph, index):
    for value in graph[index]:
        combo = []
        if (value + index == (len(graph)*2)-1):
            combo.append(value)
            return combo
        elif (value + index > len(graph)):
            continue
        combo = recurse(graph, value+index)
        combo.append(value)
        return combo


class MemoryTable:
    def __init__(self, stores, length): #length is amount of items
        self.length = length
        self.memory = []
        for i in range(stores):
            col = []
            for j in range(2 ** length):
                col.append(0)
            self.memory.append(col)

    #appends all the sellers combinations of items to a 2d array
    def append(self, seller, numberedSeller, quantitiesNeeded):
        for i in range(len(self.memory[numberedSeller])):
            self.memory[numberedSeller][i] = seller.priceOf(i, self.length, quantitiesNeeded)

    #sorts through the memory 2d array and finds the cheapest of each column
    def find_cheapest(self):
        self.cheapest = []
        self.order = []
        self.cheapest.append(100000)
        self.order.append(-1)
        for i in range(1, len(self.memory[0])):
            value = 100000 #Placeholder as just a large value but not max to prevent rollover
            store = -1
            for j in range(len(self.memory)):
                if (self.memory[j][i] < value and self.memory[j][i] != float(0)):
                    value = self.memory[j][i]
                    store = j
            self.cheapest.append(round(value, 5))
            self.order.append(store)
        

    def bestOverall(self):
        self.OverallPrices = []
        self.OverallStores = []
        for currentVal in tqdm(range(len(self.cheapest))):
            if currentVal == 0:
                    continue
            for start in range(currentVal, len(self.cheapest)):
                total = self.cheapest[currentVal] + 5
                stores = []
                storeItem = [self.order[currentVal], currentVal]
                stores.append(storeItem)
                added = currentVal
                for index in range(start+1, len(self.cheapest)):
                    if (CheckCombine(added, index, self.length)):
                        added += index
                        total += self.cheapest[index] + 5
                        for stor in stores:
                            if (stor[0] == self.order[index]):
                                total -= 5
                        storeItem = [self.order[index], index]
                        stores.append(storeItem)
                        if (added == len(self.cheapest)-1):
                            self.OverallPrices.append(round(total, 4))
                            self.OverallStores.append(stores)
                            break

        self.bestPrice = 1
        for index in range(2, len(self.OverallPrices)):
            if (self.OverallPrices[index] <= self.OverallPrices[self.bestPrice]):
                self.bestPrice = index

    def betterOverall(self):
        self.OverallPrices = []
        self.OverallStores = []
        graph = []
        graph.append(0)
        print("Generating Graph")
        for index in tqdm(range(1, int(len(self.cheapest)/2))):
            connection = []
            for other in range(index+1, len(self.cheapest)):
                if (CheckCombine(index, other, self.length)):
                    connection.append(other)
            graph.append(connection)

        allCombos = []
        print("Creating Combinations")
        for index in tqdm(range(1, int(len(self.cheapest)/2))):
            allCombos
            recurse_call(graph, index, allCombos)
        """ print(self.cheapest)
        print(len(self.cheapest))
        print(allCombos)
        print(len(allCombos)) """
        
        for combination in allCombos:
            price = 0
            stores = []
            for number in combination:
                price += float(self.cheapest[number] + 5)
                for store in stores:
                    if (store[0] == self.order[number]):
                        price -= 5
                        break
                temp = [self.order[number], number]
                stores.append(temp)
            self.OverallPrices.append(round(price, 4))
            self.OverallStores.append(stores)

        self.bestPrice = 1
        for index in range(2, len(self.OverallPrices)):
            if (self.OverallPrices[index] <= self.OverallPrices[self.bestPrice]):
                self.bestPrice = index




    def print(self, itemIds, sellers):
        print("Total Price: $" + str(self.OverallPrices[self.bestPrice]))
        items = []
        for seller in range(len(sellers)):
            buyHere = []
            for store in self.OverallStores[self.bestPrice]:
                if (store[0] == seller):
                    binary = bin(store[1]).replace("0b", "")
                    while (len(binary) < len(itemIds)):
                        binary = "0" + binary
                    index = 0
                    #items = "Buy Items [ "
                    for char in binary:
                        if (char == '1'):
                            buyHere.append(str(itemIds[index]))
                        index += 1
            items.append(buyHere)
        for item in range(len(items)):
            if (len(items[item]) == 0):
                continue
            print("Buy Items " + str(items[item]) + " from " + sellers[item].url)
        

#This stores a seller's information
class Seller:
    #initializes the url, prices and quantities and runs get_prices
    def __init__(self, url, itemIds, colors):
        if (len(itemIds) == 0):
            jsn = json.loads(url)
            self.url = jsn["url"]
            self.prices = jsn["prices"]
            self.quantities = jsn["quantities"]
            self.minBuy = jsn["minBuy"]
        else:
            self.url = url
            self.prices = []
            self.quantities = []
            self.minBuy = float(0)

            self.get_prices(itemIds, colors)

    #scrapes through the seller's store page for each item and collects the information
    def get_prices(self, itemIds, colors):
        for item in range(len(itemIds)): #goes through each item
            endpoint = self.url + "o={\"q\":\"" + str(itemIds[item]) + "\",\"colorIDFilter\":" + str(colors[item]) + ",\"showHomeItems\":0}" #Used to generate each item's given store link
            browser.get(endpoint)
            time.sleep(1.1) #insures that the DOL for the page loads fully and IP doesn't get blocked too soon

            #takes the page data (same as inspect element rather than page source)
            content=browser.find_element("xpath", "//*") 
            source_code = content.get_attribute("outerHTML")

            #finds the minimum buy for the store
            minimum = source_code[source_code.find("minBuy:")+11:source_code.find("minBuy:")+20]
            if (minimum.find("US ") == -1):
                self.minBuy = float(0)
            else:
                self.minBuy = float(minimum[4: minimum.find("\'")])

            #searches for the buy class in the html and then locates the price and quantity of the item
            soup = BeautifulSoup(source_code, 'html.parser')
            pricing = str(soup.find(class_="buy"))
            if (pricing.find("US ") == -1): #if item is not available
                self.prices.append(float(-1))
                self.quantities.append(0)
            else:
                start = pricing.find("US ")+4
                self.prices.append(float(pricing[start:start + pricing[start: len(pricing)].find("</strong>")]))
                start = pricing.find("</span><strong><span>")+21
                self.quantities.append(int(pricing[start:start + pricing[start: len(pricing)].find("</span>")].replace(',', "")))

    #Not used but still good to have, just prints the info of the seller
    def print(self):
        print(self.url + "      $" + str(self.minBuy))
        print(self.prices)
        print(self.quantities)

    def json(self):
        output = {
            "url": self.url,
            "minBuy": self.minBuy,
            "prices": self.prices,
            "quantities": self.quantities
        }
        return json.dumps(output)

    def priceOf(self, input, length, quantitiesNeeded):
        binary = bin(input).replace("0b", "")
        output = float(0)
        while (len(binary) < length):
            binary = "0" + binary
        index = 0
        for bit in binary:
            if (bit == '1'):
                if (self.quantities[index] < quantitiesNeeded[index]):
                    output = float(0)
                    break
                output += round(self.prices[index] * quantitiesNeeded[index], 4)
            index += 1
        if (output < self.minBuy):
            return(float(0))
        return(output)

def Find_Sellers(itemIds, colors, quantities, amountOfItemsSearched, sellersPerItem):
    stores = []
    for item in tqdm(range(min(amountOfItemsSearched, len(itemIds)))):
        NoMin = "\"nmp\":1,"
        url = "https://www.bricklink.com/v2/catalog/catalogitem.page?P=" + str(itemIds[item]) + "&name=Brick%201%20x%201&category=%5BBrick%5D#T=S&C=" + str(colors[item]) + "&O={\"color\":" + str(colors[item]) + ",\"minqty\":\"" + str(quantities[item]) + "\"," + NoMin + "\"loc\":\"US\",\"ca\":\"1\",\"iconly\":0}"
        browser.get(url)
        time.sleep(2)
        content=browser.find_element("xpath", "//*")
        source_code = content.get_attribute("outerHTML")
        soup = BeautifulSoup(source_code, 'html.parser')

        storeurls = []
        for link in soup.find_all('tr', class_="pciItemContents"):
            storeurls.append(str(link))

        if (False):
            file = open("output.txt", "r")
            while True:
                jsonString = str(file.readline())
                print(jsonString)
                if not jsonString:
                    break
                stores.append(Seller(jsonString, [], []))
        else:
            for store in range(min(sellersPerItem, len(storeurls))):
                storeurls[store] = "https:" + storeurls[store][storeurls[store].find("//store.bricklink.com/"):storeurls[store].find("itemID=")] + "#/shop?"
                stores.append(Seller(storeurls[store], itemIds, colors))

    fileText = ""      
    file = open("output.txt", "w")
    for store in range(len(stores)):
        fileText += stores[store].json() + "\n"
    file.write(fileText)
            

    file.close()
    browser.close()
    return stores
    

itemIds = ["47753", "87752", "41883", "2418a", "23448", "45301", "42060", "42061", "41765", "41764", "41748", "41747", "65768", "41531", "13547", "85970", "44676"]
colors = [11, 13, 13, 14, 13, 11, 85, 85, 85, 85, 85, 85, 11, 11, 85, 85, 85]
quantities = [1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 12, 12, 2, 5, 15]
amountOfItemsSearched = len(itemIds)
sellersPerItem = 2
validStores = Find_Sellers(itemIds, colors, quantities, amountOfItemsSearched, sellersPerItem)
""" for store in validStores:
    store.print() """

memory = MemoryTable(len(validStores), len(itemIds))
for seller in range(len(validStores)):
    memory.append(validStores[seller], seller, quantities)
memory.find_cheapest()
#memory.bestOverall()
memory.betterOverall()
memory.print(itemIds, validStores)