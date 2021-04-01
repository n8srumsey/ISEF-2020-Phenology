[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]



<!-- PROJECT LOGO -->
<br />
<p align="center">
  <a href="https://github.com/n8srumsey/ISEF-2020-Phenology">
    <img src="readme_images/logo.png" alt="Analytics System" width=80>
  </a>

  <h3 align="center"><b>Machine-Learning Powered Spatiotemporal Analytics System for Deciduous Forest Phenology</b></h3>

  <p align="center">
    <i>A suite of analysis tools using machine learning to study the trends and pattern in phenology of deciduous forests.</i>
    <br />
    <br />
    <a href="https://github.com/n8srumsey/ISEF-2020-Phenology/issues">Report Bug</a>
    ·
    <a href="https://github.com/n8srumsey/ISEF-2020-Phenology/issues">Request Feature</a>
  </p>
<br />
<br />
</p>




<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary><h2 style="display: inline-block">Table of Contents</h2></summary>
  <ol>
    <li> 
      <a href="#abstract">Abstract</a>
    </li>
    <li>
      <a href="#analytics-system">Analytics System</a>
      <ul>
        <li><a href="#features">Features</a></li>
        <ul><li><a href="#data-management">Data Management</a></li>
        <li><a href="#site-analysis">Site Analysis</a></li>
        <li><a href="#aggregate-analysis">Aggregate Analysis</a></li>
        <li><a href="#spatial-analysis">Spatial Analysis</a></li>
      </ul>
      <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## Abstract
Shifts in plant phenology provide compelling evidence that ecosystems and species are influenced by climate change. In this project I present a system using machine learning to assist in the study and observation of deciduous forest phenology.

I employed a deep Convolutional Neural Network (CNN) to classify the current phenophase of deciduous forests from a single image, trained using early stopping and k-fold cross validation. The CNN achieved a best accuracy of 60.67%, precision of 60.66%, recall of 60.65%, and F1 Score of 60.66% on the validation dataset. These results exhibited considerably lower performance than published literature. This can be primarily attributed to a faulty dataset, containing frequently mislabeled samples and unrelated images. To address this issue best in the future, the dataset should be curated manually to remove any problematic samples. Additionally, in future work transfer learning should be employed to reduce the overhead of training, so that features do not need to be trained from scratch, decreasing the sensitivity of the CNN to issues in the dataset.

I then developed a website containing an analytics suite which provides analyses based on a timeseries of images of a deciduous forest. The website includes local site, aggregate, and spatial analyses to provide unique insight into the spatiotemporal trends of deciduous forest phenology, using the timeseries of images classified according to phenophase of the deciduous forest. My analyses elucidated spatiotemporal patterns in an earlier bud-burst phenophase consistent with climate-change predictions, demonstrating the potential utility of this analytical suite in assisting researchers.  

## Analytics System

<img src="readme_images/HomePage.png">

### **Features**

### Data Management

<img src="readme_images/DataManagement.png"> 

- Manage your phenology data across multiple locations.
- Upload images from the site to take advantage of machine learning algorithms to classify and determine phenophases and transition dates.

### Site Analysis

<img src="readme_images/SiteAnalysis1.png">

- Analyize site phenophase onset and duration trends.
- Select a site to view tables and graphs of bud burst and leaf senescence onset dates and durations, as well as view images of the site at said phenophase transition dates.

### Aggregate Analysis

<img src="readme_images/AggregateAnalysis.png">

- Analyize aggregate phenophase onset and duration trends.
- View tables and graphs of the average bud burst and leaf senescence onset dates and durations, across all sites as well as view images of the site at said phenophase transition dates.

### Spatial Analysis

<img src="readme_images/SpatialAnalysis.png">

- Analyize spatial trends of bud burst and leaf senescence phenophases across multiple sites.
- Using an interactive GIS map, view the spatial patterns between sites' locations of onset dates and durations of bud burst and leaf senescence phenophases.

### Built With

* [TensorFlow](https://www.tensorflow.org/)
* [Django](https://www.djangoproject.com/)
* [Bootstrap](https://getbootstrap.com/)
* [ArcGIS](https://developers.arcgis.com/javascript/latest/)



<!-- GETTING STARTED -->
## Getting Started

Steps to set up the project as is. Please note that this project was not developed for others to set up individually - it was a proof-of-concept engineering project.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.

* [Python 3.8](https://www.python.org/)
* [CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
* [cuDNN](https://developer.nvidia.com/cudnn)
* [Anaconda](https://anaconda.org)

### Installation

1. Clone the repo

   ```sh
   git clone https://github.com/gn8srumsey/ISEF-2020-Phenology.git
   ```

2. Install Python packages

   ```sh
    conda env create n8srumsey/isef-2020
    conda activate isef-2020
   ```

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<!-- CONTACT -->
## Contact

Nathan Rumsey - nathan.s.rumsey@gmail.com

Project Link: [https://github.com/n8srumsey/ISEF-2020-Phenology](https://github.com/n8srumsey/ISEF-2020-Phenology)

[contributors-shield]: https://img.shields.io/github/contributors/n8srumsey/ISEF-2020-Phenology.svg?style=for-the-badge
[contributors-url]: https://github.com/n8srumsey/ISEF-2020-Phenology/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/n8srumsey/ISEF-2020-Phenology.svg?style=for-the-badge
[forks-url]: https://github.com/n8srumsey/ISEF-2020-Phenology/network/members
[stars-shield]: https://img.shields.io/github/stars/n8srumsey/ISEF-2020-Phenology.svg?style=for-the-badge
[stars-url]: https://github.com/n8srumsey/ISEF-2020-Phenology/stargazers
[issues-shield]: https://img.shields.io/github/issues/n8srumsey/ISEF-2020-Phenology.svg?style=for-the-badge
[issues-url]: https://github.com/n8srumsey/ISEF-2020-Phenology/issues
[license-shield]: https://img.shields.io/github/license/n8srumsey/ISEF-2020-Phenology?label=license&style=for-the-badge
[license-url]: https://github.com/n8srumsey/ISEF-2020-Phenology/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/nathan-rumsey-66ab1320a/

