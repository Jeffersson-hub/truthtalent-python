# Ajoutez dans la classe SupabaseHandler

def upload_to_storage(self, file_content: bytes, file_hash: str, filename: str) -> Dict:
        """Upload un fichier vers Supabase Storage"""
        try:
            bucket_name = "cvs"
            file_path = f"{file_hash}_{filename}"
            
            # Upload vers Supabase Storage
            response = self.client.storage.from_(bucket_name).upload(
                file_path, 
                file_content,
                {"content-type": "application/pdf"}
            )
            
            # Générer l'URL publique
            public_url = self.client.storage.from_(bucket_name).get_public_url(file_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "public_url": public_url,
                "bucket": bucket_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }