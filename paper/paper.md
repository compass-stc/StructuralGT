---
title: 'StructuralGT: A Python API for graph-based design of complex materials'
tags:
  - Python
  - Graph theory
  - Materials science
  - Structure-property relations
authors:
  - name: Alain Kadar
    orcid: 0000-0002-0522-4199
    affiliation: "1, 2" # (Multiple affiliations must be quoted)
  - name: Sharon C. Glotzer
    orcid: 0000-0002-7197-0085
    affiliation: "1, 2"
  - name: Nicholas A. Kotov
    orcid: 0000-0002-6864-5804
    corresponding: true # (This is how to denote the corresponding author)
    affiliation: "1, 2"
affiliations:
 - name: Department of Chemical Engineering, University of Michigan, Ann Arbor, Michigan 48109, United States
   index: 1
 - name: NSF Center for Complex Particle Systems (COMPASS), Ann Arbor, Michigan 48109, United States
   index: 2
date: 1 August 2025
bibliography: paper.bib
---

# Summary

*StructuralGT* provides a set of tools for the quantitative analysis of complex materials combining order and disorder, relying extensively on methods from graph theory (GT). Many such materials are made from nanoscale components self-assembled into gels and other particle networks whose structure is particularly difficult to describe using the traditional toolbox of colloidal chemistry and soft matter. This release includes 3D capabilities, new descriptors, analysis of segmented tomography, and an optimized backend, all of which improve upon the *StructuralGT* GUI application released by @Vecchio2021.  Additionally, this contribution details the development of a customizable and extensible API, which exposes the entire data-to-network workflow, along with modular tools for analysis of the resulting graphs. The Python API makes calls to either fast C++ libraries or *StructuralGT* scripts, while the advanced user has the option to incorporate their own C++ scripts using the provided template wrapper. Finally, *StructuralGT* writes the analyzed graphs to a geometry-preserving filetype allowing for storage and easy visualization of the data with the OVITO desktop application [@ovito]. *StructuralGT* binaries are maintained on conda-forge [@SGT-conda], and the open-source repository (along with a repository of *StructuralGT* examples) is hosted on the GitHub organization page for the Center for Complex Particle Systems [@COMPASS-github]. Documentation is hosted on read-the-docs [@SGT-docs].

# Statement of Need

Many advanced materials essential for sustainability, exemplified by a wide range of self-assembled biomimetic nanostructures produced by self-assembly, exhibit long-range connectivity patterns, non-random disorder, and hierarchical complexity, and so a quantitative basis in which to represent their structure is needed. Particularly for nanomaterials, the  analysis of network structures has repeatedly been shown to benefit from a GT-based representation of their 2D data [@Zhang2020; @Zhang2021; @Vecchio2022]. As 3D imaging becomes increasingly accessible to experimental communities, tools for their larger and higher-dimensional analyses are needed. The utility of GT in the context of structural representation has already been demonstrated [@Duan2023; @Kalutantirige2024]. The further extension of structural representation to property predictions requires tools specific to each system, motivating the development of a modular and extensible user-facing API. This also allows for bundling scripts with research publications, thus fulfilling the growing need for reproducible scientific computing. Collectively, these requirements necessitate the development of the present contribution, whose uses to date include the prediction of charge transport properties of silver nanowire networks [@Wu2024]; the prediction of stress distribution in strut-lattices [@ReyesMartinez2025]; and the rationalization of non-monotonic chiroptical properties of complex nanodendrimers [@Kuznetsova2025].

# Summary of Features

## Graph Extraction and Descriptors
The structure of complex materials  can be represented by a graph, i.e. a mathematical object containing a set of nodes and edges connecting them. Unlike most graphs, a GT-based description of complex materials is embedded in Cartesian 2 or 3D space. Besides the information about connectivity, the GT representations of materials have essential geometrical information associated with both nodes and edges. Both topological and geometrical information can be directly extracted from the experimental data, and specifically from the atomic force microscopy, electron microscopy, confocal microscopy, and other techniques, which dramatically increases accuracy and specificity of GT descriptions of materials. To most effectively represent the information encapsulated in GT descriptors of materials most often organized as a matrix, we developed the ``NetworkMaterial`` object. The ``NetworkMaterial`` object can be populated with a ``graph`` attribute that contains the connectivity information capturing much of the material's structure. Development of the ``NetworkMaterial`` object is motivated by the need to preserve information lost during abstractions of material structure as a graph. Computational methods of the ``NetworkMaterial`` object that allow the graph extraction involve image processing, skeletonization, and neighbor finding. Once the appropriate methods have been called, the ``graph`` attribute of the ``NetworkMaterial`` object is populated. The graph may be visualized and/or stored in a manner which preserves the underlying geometric and topological complexity of the material's structure. An example involving image processing and steps required to produce a simple heatmap of nodes colored by degree, is given in Figure \ref{fig:workflow}.

![The workflow of complex material analysis with *StructuralGT* is exemplified using a network of nanowires. A `NetworkMaterial` object is first instantiated with a filepath (top-left). When analyzing experimental images, the `NetworkMaterial` object must binarize and skeletonize the image (bottom). Binarization is made possible by defining a set of image processing parameters. These can be determined with trial-and-error, using the `Binarizer` object. The subsequent skeletonization step is relatively parameter free (but special options are defined in the documentation). The graph can then be extracted by tracing the skeleton to classify pixels (or voxels) as belonging to nodes or edges. The `NetworkMaterial` object can then be combined with a `Compute` object (e.g. `Degree`) to calculate results. When both the `set_graph` method of the `NetworkMaterial` object and the `compute` method of the `Compute` object have been called, they can be combined to write annotated network files and plot heatmaps (bottom-right). Experimental micrograph taken from @Wu2024.\label{fig:workflow}](fig2.png)

## Compute Objects
Once the graph attribute of a ``NetworkMaterial`` object has been populated (i.e. a GT-based representation of the complex material is created), it can be combined with the ``Compute`` objects to carry out analysis of the system. Alternatively, the user may generate a ``graph`` populated ``NetworkMaterial`` object by loading from the network filetype discussed in the next section. In either case, a loaded ``NetworkMaterial`` can be combined with ``Compute`` objects to perform different analyses. The current list of ``Compute`` objects is summarized below:
\begin{itemize}
\item ``Structural``: This object is mainly a wrapper for standard GT parameters, as calculated by igraph. It can be used to quantitatively establish structural differences between materials synthesized in different conditions (e.g. \citeproc{ref-Kuznetsova2025}{Kuznetsova et al., 2025}).
\item ``Electronic``: This object can be used for solving general networked linear transport problems in  or 3D. Recently, it was used to simulate the four-point probe experiments carried out to assess electrical properties of 2D conductive films, and reproduced experimental results (\citeproc{ref-Wu2024}{Wu et al., 2024}).
\item ``Geometric``: This object is for assessing orientational order in networks, which often occurs when densely packed edges are forced into alignment, often resulting in anisotropic properties impossible to detect with traditional GT metrics (e.g. \citeproc{ref-Wu2024}{Wu et al., 2024}).
\item ``Betweenness``: This object provides betweenness parameters and variations that are designed to predict hotspots in stressed networks (e.g. \citeproc{ref-ReyesMartinez2025}{Reyes-Martinez et al., 2025}).
\item ``AverageNodalConnectivity``: Due to the significant computational cost, computations for average nodal connectivity are relegated to their own object. This object provides fast calculation of the average nodal connectivity, which has been shown to correlate with the mechanical properties of gels (e.g. \citeproc{ref-Vecchio2022}{Vecchio et al., 2022}).
\end{itemize}

Depiction of their combination with ``NetworkMaterial`` objects is given in Figure \ref{fig:api}.

![*StructuralGT* obtains results by combining an object that represents the system (`NetworkMaterial`) and an object that carries out some computation (`Compute`). NetworkMaterial objects are generated either from micrographs or (potentially dynamic) point cloud data. Compute objects are written to carry out computations not typically included in standard graph theory libraries. Additionally, once the `NetworkMaterial` object has been populated with the `graph` attribute, traditional GT parameters can be calculated via calls to the igraph library (e.g. degree, closeness, clustering coefficient). Experimental micrograph taken from @Wu2024.\label{fig:api}](API.png)

## Network Material Filetype
While there are many filetypes designed for storing graphs, the requirement of preserving geometry in graphs extracted from material networks actually makes molecular simulation filetypes a more appropriate choice. For *StructuralGT*, we have opted for the ``.gsd`` format, because its compatibility with the OVITO toolkit allows us to make rich and dynamic visualizations with both the desktop application and their extensive Python API [@ovito].

## C++/Python Bindings
Advanced users may wish to write their own C++ scripts and integrate them with *StructuralGT*. Doing so is made possible using wrappers provided with *StructuralGT*. These wrappers were used to implement the ``Betweenness`` and ``AverageNodalConnectivity`` objects. Their general structure is outlined in the *StructuralGT* documentation [@SGT-docs].

## Acknowledgements

All authors are grateful for support from the U.S. National Science Foundation under Cooperative Agreement No. 2243104, “Center for Complex Particle Systems (COMPASS)” Science and Technology Center. Additionally, we would like to acknowledge Drew Vecchio for implementing the initial release of this software and answering any questions we had about it. We would like to acknowledge Joshua Anderson who mentored the implementation of C++/Python bindings, deployment to conda-forge, and software engineering best-practices. We would like to acknowledge the developers of the freud library, [@Ramasubramani2020] whose choice to partition analysis into system-like and compute-like objects in their own library inspired the *StructuralGT* API. Finally we would like to acknowledge the Glotzer Group and Kotov Lab students who used initial prototypes of *StructuralGT* and gave feedback on how it could be improved, particularly Linlin Sun and Joshua Anderson who both gave feedback for this manuscript.

# References
