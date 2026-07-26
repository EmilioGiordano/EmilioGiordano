<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/EmilioGiordano/EmilioGiordano/main/assets/banner-dark.svg">
    <img src="https://raw.githubusercontent.com/EmilioGiordano/EmilioGiordano/main/assets/banner-light.svg" alt="Emilio Giordano" width="100%">
  </picture>
</p>

Finishing a Bachelor's degree in Computer Science (Licenciatura en Informática) at [UNSAdA](https://www.unsada.edu.ar/), Buenos Aires.

[LinkedIn](https://www.linkedin.com/in/emilio-giordano/) &nbsp;·&nbsp; [bento.me/emiliogiordano](https://bento.me/emiliogiordano) &nbsp;·&nbsp; [giordanoemilio21@gmail.com](mailto:giordanoemilio21@gmail.com)

## Things I've built

<table>
<tr>
<td colspan="2" valign="top">

**[LEGO Gallery](https://legogallery.vercel.app/)**

A browser engine that replays LEGO models as assembly sequences. A Python pipeline flattens a Mecabricks export into a compact runtime format: it walks the object hierarchy multiplying local matrices by their ancestors to recover each part's world transform, then groups parts by geometry and material so a shape is stored once and every occurrence costs one matrix. Flexible parts that rely on deformation data Three.js can't use keep their Bézier control points and get rebuilt as tube geometry in the browser.

At runtime one `InstancedMesh` per geometry/material pair draws thousands of bricks without a draw call each. The choreography is deterministic: a hash of each part's stable index seeds its orbit, radius and timing, so a reload reproduces the same assembly rather than a fresh random cloud. Two sets so far, and adding one is data rather than code.

<sub>Three.js · instanced WebGL · no bundler, no backend<br>[Live](https://legogallery.vercel.app/) · [Code](https://github.com/EmilioGiordano/lego-gallery)</sub>

</td>
</tr>
<tr>
<td width="50%" valign="top">

**[DBiewer](https://github.com/EmilioGiordano/DBiewer)**

Paste PostgreSQL DDL, get a diagram back. I was tired of reading schemas as walls of syntax and not being able to see them, so I made the tool I wanted.

<sub>JavaScript<br>[Code](https://github.com/EmilioGiordano/DBiewer)</sub>

</td>
<td width="50%" valign="top">

**[Dijkstra & A\*](https://dijsktra-astar-star-wars.netlify.app/)**

Two pathfinders searching a galaxy map side by side, so you can see exactly where the heuristic saves A\* the work. Dressed in the interface language of Jedi: Fallen Order.

<sub>JavaScript<br>[Live](https://dijsktra-astar-star-wars.netlify.app/) · [Code](https://github.com/EmilioGiordano/Star-Wars-Galaxy-dijkstra-and-A-algorithms-)</sub>

</td>
</tr>
<tr>
<td width="50%" valign="top">

**[Sieve benchmark](https://criba-expo.netlify.app/)**

The Sieve of Eratosthenes written five times over and timed against itself, so the gap between a systems language and a scripting one stops being an opinion.

<sub>Rust · Java · C · Python · NumPy<br>[Live](https://criba-expo.netlify.app/) · [Code](https://github.com/EmilioGiordano/criba-benchmark)</sub>

</td>
<td width="50%" valign="top">

**[Postopenman](https://github.com/EmilioGiordano/Postopenman)**

An API client with a Rust core and a Svelte front end.

<sub>Rust · Svelte<br>[Code](https://github.com/EmilioGiordano/Postopenman)</sub>

</td>
</tr>
<tr>
<td colspan="2" valign="top">

**[Tower of Hanoi](https://hanoi-tower-eg.vercel.app/)** &nbsp; The puzzle, playable in the browser. &nbsp; <sub>[Live](https://hanoi-tower-eg.vercel.app/)</sub>

</td>
</tr>
</table>

## Notes I keep in public

Coursework I wrote up properly instead of leaving it in a notebook. Written in Spanish.

- **[Cisco device commands](https://emiliogiordano.github.io/Hoja-de-Trucos-Cisco-Packet-Tracer/):** switches, routers, VLANs and routing protocols in Packet Tracer.
- **[Declarative programming](https://emiliogiordano.github.io/Programacion-Declarativa-Practica/):** Prolog and Scheme, covering syntax, lists and recursion.
- **[The XOR swap](https://emiliogiordano.github.io/XOR-swap/):** exchanging two variables without a third one.

<br>

<sub>The banner is a distance field measured outward from the letterforms, plus a real Dijkstra shortest path that crosses at the space in the name. <a href="https://github.com/EmilioGiordano/EmilioGiordano/blob/main/assets/banner.py">Generated here</a>.</sub>
