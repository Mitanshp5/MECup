import os
import sys
import datetime
import json

# Add backend directory to sys.path to allow imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from database import SessionLocal, engine
from plc import models as plc_models

def migrate_scans():
    db = SessionLocal()
    try:
        plc_models.Base.metadata.create_all(bind=engine)
        
        captured_dir = os.path.join(backend_dir, "captured_images")
        
        if not os.path.exists(captured_dir):
            print("No captured_images directory found.")
            return

        print(f"Scanning {captured_dir} for existing scans...")
        
        count = 0
        folders = sorted(os.listdir(captured_dir))
        
        for folder_name in folders:
            folder_path = os.path.join(captured_dir, folder_name)
            if not os.path.isdir(folder_path) or not folder_name.startswith("scan_"):
                continue
                
            # Check if scan already exists in DB
            existing = db.query(plc_models.Scan).filter(plc_models.Scan.id == folder_name).first()
            if existing:
                # print(f"Skipping {folder_name} (already in DB)")
                continue
                
            print(f"Migrating {folder_name}...")
            
            # Parse Metadata
            try:
                timestamp_str = folder_name.replace("scan_", "")
                dt = datetime.datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            except:
                dt = datetime.datetime.utcnow()
                
            scanned_by = "Unknown"
            info_path = os.path.join(folder_path, "scan_info.json")
            if os.path.exists(info_path):
                try:
                    with open(info_path, 'r') as f:
                        info = json.load(f)
                        scanned_by = info.get("scanned_by", "Unknown")
                except:
                    pass
            
            scan = plc_models.Scan(
                id=folder_name,
                start_time=dt,
                scanned_by=scanned_by,
                batch_folder=folder_path,
                status="pass", 
                defect_count=0,
                image_count=0
            )
            
            # Process Images
            image_count = 0
            defect_count = 0
            
            results_dir = os.path.join(folder_path, "results")
            
            # Map of image base name to defect info
            defect_map = {}
            if os.path.exists(results_dir):
                for f in os.listdir(results_dir):
                    if f.endswith("_meta.json"):
                        try:
                            with open(os.path.join(results_dir, f), 'r') as jf:
                                meta = json.load(jf)
                                base_image = meta.get("image", "")
                                base_image = os.path.basename(base_image)
                                
                                d_count = meta.get("defect_count", 0)
                                if d_count > 0:
                                    defect_map[base_image] = {
                                        "count": d_count,
                                        "overlay": f.replace("_meta.json", "_overlay.png")
                                    }
                        except:
                            pass

            for f in os.listdir(folder_path):
                if f.endswith(".jpg"):
                    image_count += 1
                    img_defects = 0
                    has_defects = False
                    overlay = None
                    
                    if f in defect_map:
                        img_defects = defect_map[f]["count"]
                        has_defects = True
                        overlay = os.path.join(results_dir, defect_map[f]["overlay"])
                        defect_count += img_defects
                    
                    scan_image = plc_models.ScanImage(
                        scan_id=folder_name,
                        filename=f,
                        filepath=os.path.join(folder_path, f),
                        defect_count=img_defects,
                        has_defects=has_defects,
                        overlay_path=overlay
                    )
                    db.add(scan_image)
            
            scan.image_count = image_count
            scan.defect_count = defect_count
            if image_count > 0 and defect_count > (image_count / 10):
                 scan.status = "fail"
            
            db.add(scan)
            count += 1
            
        db.commit()
        print(f"Migration complete. {count} scans added.")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_scans()
