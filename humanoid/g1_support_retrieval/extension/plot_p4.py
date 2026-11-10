"""Plot recorded physical motion; no planned trajectory is presented as measured."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Rectangle
from .verify_p4 import corners


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument("directory",type=Path)
    args=parser.parse_args(); root=args.directory
    profile=json.loads((root/"profile.json").read_text())
    rows=json.loads((root/"execution/trace.json").read_text())
    times=np.array([r["time"] for r in rows]); target=np.array([r["box"] for r in rows]); robot=np.array([r["root"] for r in rows])
    center=np.array(profile["goal"]["center_xy_m"]); size=np.array(profile["goal"]["size_xy_m"]); lo=center-size/2;hi=center+size/2
    fig,axs=plt.subplots(2,2,figsize=(12,8),layout="constrained")
    ax=axs[0,0];ax.add_patch(Rectangle(lo,*size,facecolor="#d8f2d8",edgecolor="green",label="D"))
    ax.plot(target[:,0],target[:,1],color="#b66b25",label="target center")
    ax.plot(robot[:,0],robot[:,1],color="#285caf",label="robot root")
    for row,alpha,label in ((rows[0],.2,"target start"),(rows[-1],.6,"target end")):
        pts=corners(np.array(row["box"]),np.array(row["box_quat"]),profile["target"]["size_m"])
        pts=pts[[0,2,6,4],:2]
        ax.add_patch(Polygon(pts,facecolor="#b66b25",alpha=alpha,label=label))
    ax.set(xlabel="x / m",ylabel="y / m",title="Measured floor-plane motion",aspect="equal");ax.legend(fontsize=8)
    margins=[]
    for r in rows:
        pts=corners(np.array(r["box"]),np.array(r["box_quat"]),profile["target"]["size_m"])
        margins.append(min(float((pts[:,:2]-lo).min()),float((hi-pts[:,:2]).min())))
    ax=axs[0,1];ax.plot(times,margins,color="#b66b25");ax.axhline(0,color="black",ls="--",lw=.8)
    ax.set(xlabel="simulation time / s",ylabel="minimum whole-object D margin / m",title="Positive margin: all target corners inside D")
    ax=axs[1,0];ax.plot(times,[r["box_speed"] for r in rows],label="target linear speed")
    ax.plot(times,[np.linalg.norm(r["root_linear_velocity"]) for r in rows],label="robot linear speed")
    ax.axhline(.03,color="black",ls="--",lw=.8,label="terminal 0.03 m/s bound")
    ax.set(xlabel="simulation time / s",ylabel="m/s",title="Measured linear velocities");ax.legend(fontsize=8)
    ax=axs[1,1]
    ax.plot(times,[r["support_contacts"]["target_ground_fz_N"] for r in rows],label="target ground normal")
    for i,name in enumerate(("left foot","right foot")):
        ax.plot(times,[r["support_contacts"]["feet_ground_fz_N"][i] for r in rows],label=name,alpha=.8)
    ax.set(xlabel="simulation time / s",ylabel="normal support force / N",title="Actual contact support");ax.legend(fontsize=8)
    for ax in axs.flat:ax.grid(alpha=.2)
    fig.suptitle(f"H1S-07.P4 · {root.name} · measured Genesis GPU trajectory",fontsize=14)
    output=root/"trajectory_overview.png";fig.savefig(output,dpi=160);plt.close(fig)
    print(output)

if __name__=="__main__":main()
