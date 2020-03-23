# -*- coding: utf-8 -*-
"""
Created on Mon Mar 23 13:21:48 2020

@author: Craig Dickson - @craigdoesdata
Developed after / with Abdi Shakur's guide here: https://towardsdatascience.com/how-to-calculate-travel-time-for-any-location-in-the-world-56ce639511f 
and here: https://github.com/shakasom/isochronewithosmnx/tree/ab7e8415279235bf9cb3c50ac8770d418be66581
"""

import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from descartes import PolygonPatch
from IPython.display import IFrame
ox.config(log_console=True, use_cache=True)



def create_graph(loc, dist, transport_mode, loc_type="address"):
    # Transport mode = ‘walk’, ‘bike’, ‘drive’, ‘drive_service’, ‘all’, ‘all_private’, ‘none’
    if loc_type == "address":
        G = ox.graph_from_address(loc, distance=dist, network_type=transport_mode)
    elif loc_type == "points":
        G = ox.graph_from_point(loc, distance=dist, network_type=transport_mode )
    return G

loc1 = input('Please enter the location you are interested in (address, city name, coordinates):')
# dist = input('Please enter the distance you would like to see plotted, in metres:')
transport_mode1 = input('Please enter the mode of transport you wish to use (walk, bike, drive):')

# travel speed speed in km/hour and map scale
if transport_mode1 == 'walk':
    travel_speed = 4.5
    dist1 = 5000
elif transport_mode1 == 'bike':
    travel_speed = 23
    dist1 = 10000
elif transport_mode1 == 'drive':
    travel_speed = 60
    dist1 = 100000



G = create_graph(loc= loc1, 
                 dist= dist1, 
                 transport_mode= transport_mode1, 
                 )

# fig, ax = ox.plot_graph(G);
# plt.tight_layout()

# Create nodes geodataframe from Graph network (G)
gdf_nodes = ox.graph_to_gdfs(G, edges=False)

user_point = ox.geocode(loc1)

# Specify where you want to start and get nearest nodes. 
point_of_interest = ox.get_nearest_node(G, point=user_point)

# Project a graph from lat-long to the UTM zone appropriate for its geographic location.
G = ox.project_graph(G)

# Trip time in Minutes
trip_times = [5, 15, 25, 40, 60]

# add an edge attribute for time in minutes required to traverse each edge
meters_per_minute = travel_speed * 1000 / 60 #km per hour to m per minute
for u, v, k, data in G.edges(data=True, keys=True):
    data['time'] = data['length'] / meters_per_minute


# get one color for each isochrone
iso_colors = ox.get_colors(n=len(trip_times), cmap='plasma', start=0.3, return_hex=True)


# color the nodes according to isochrone then plot the street network
node_colors = {}
for trip_time, color in zip(sorted(trip_times, reverse=True), iso_colors):
    subgraph = nx.ego_graph(G, point_of_interest, radius=trip_time, distance='time')
    for node in subgraph.nodes():
        node_colors[node] = color

nc = [node_colors[node] if node in node_colors else 'none' for node in G.nodes()]
ns = [10 if node in node_colors else 0 for node in G.nodes()]
# fig, ax = ox.plot_graph(G, fig_height=8, node_color=nc, node_size=ns, save=True, node_alpha=0.8, node_zorder=2)


# make the isochrone polygons
isochrone_polys = []
for trip_time in sorted(trip_times, reverse=True):
    subgraph = nx.ego_graph(G, point_of_interest, radius=trip_time, distance='time')
    node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
    bounding_poly = gpd.GeoSeries(node_points).unary_union.convex_hull
    isochrone_polys.append(bounding_poly)
    
# plot the network then add isochrones as colored descartes polygon patches
fig, ax = ox.plot_graph(G, fig_height=80, show=False, close=False, save=True, edge_color='k', edge_alpha=0.7, node_color='none')
for polygon, fc in zip(isochrone_polys, iso_colors):
    patch = PolygonPatch(polygon, fc=fc, ec='none', alpha=0.6, zorder=-1)
    ax.add_patch(patch)
plt.show()