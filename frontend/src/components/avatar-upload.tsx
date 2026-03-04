"use client";

import { useState, useCallback, useRef } from "react";
import Cropper from "react-easy-crop";
import type { Area } from "react-easy-crop";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Camera, Loader2, Trash2 } from "lucide-react";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Create a cropped image blob from a source image URL and crop area.
 */
async function getCroppedBlob(imageSrc: string, crop: Area): Promise<Blob> {
  const image = new Image();
  image.src = imageSrc;
  await new Promise<void>((resolve, reject) => {
    image.onload = () => resolve();
    image.onerror = reject;
  });

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d")!;

  // Output 512×512 for a good quality profile picture
  const size = 512;
  canvas.width = size;
  canvas.height = size;

  ctx.drawImage(
    image,
    crop.x,
    crop.y,
    crop.width,
    crop.height,
    0,
    0,
    size,
    size,
  );

  return new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) resolve(blob);
        else reject(new Error("Canvas toBlob failed"));
      },
      "image/webp",
      0.9,
    );
  });
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface AvatarUploadProps {
  /** Current profile picture URL (pre-signed or local). */
  imageUrl?: string | null;
  /** Fallback initials when no image. */
  initials: string;
  /** Called with the cropped file to upload. Should throw on error. */
  onUpload: (file: File) => Promise<void>;
  /** Called to delete the current picture. Should throw on error. */
  onDelete?: () => Promise<void>;
  /** Extra Tailwind classes for the outer avatar container. */
  className?: string;
  /** Whether the user can upload/delete (e.g. admin check). Default: true. */
  editable?: boolean;
}

export function AvatarUpload({
  imageUrl,
  initials,
  onUpload,
  onDelete,
  className = "h-16 w-16",
  editable = true,
}: AvatarUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [rawImage, setRawImage] = useState<string | null>(null);
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedArea, setCroppedArea] = useState<Area | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const onCropComplete = useCallback(
    (_croppedAreaPercentage: Area, croppedAreaPixels: Area) => {
      setCroppedArea(croppedAreaPixels);
    },
    [],
  );

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    // Basic client-side validation
    const allowedTypes = ["image/jpeg", "image/png", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      // 10 MB raw limit (will be cropped + compressed)
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setRawImage(reader.result as string);
      setCrop({ x: 0, y: 0 });
      setZoom(1);
      setDialogOpen(true);
    };
    reader.readAsDataURL(file);
    // Reset so re-selecting the same file works
    e.target.value = "";
  }

  async function handleConfirmCrop() {
    if (!rawImage || !croppedArea) return;
    setIsUploading(true);
    try {
      const blob = await getCroppedBlob(rawImage, croppedArea);
      const file = new File([blob], "profile.webp", { type: "image/webp" });
      await onUpload(file);
      setDialogOpen(false);
      setRawImage(null);
    } catch {
      // Error handling is expected to be done in onUpload (toast etc.)
    } finally {
      setIsUploading(false);
    }
  }

  function handleCancel() {
    setDialogOpen(false);
    setRawImage(null);
  }

  return (
    <>
      <div className="relative group inline-block">
        <Avatar className={className}>
          {imageUrl && <AvatarImage src={imageUrl} alt="Profile picture" />}
          <AvatarFallback className="bg-primary text-primary-foreground text-xl">
            {initials}
          </AvatarFallback>
        </Avatar>

        {editable && (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="absolute inset-0 flex items-center justify-center rounded-full bg-black/50 opacity-0 transition-opacity group-hover:opacity-100 cursor-pointer"
            aria-label="Change picture"
          >
            <Camera className="h-5 w-5 text-white" />
          </button>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      <Dialog
        open={dialogOpen}
        onOpenChange={(open) => !open && handleCancel()}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Crop picture</DialogTitle>
            <DialogDescription>
              Drag to reposition and use the slider to zoom.
            </DialogDescription>
          </DialogHeader>

          <div className="relative w-full aspect-square bg-muted rounded-md overflow-hidden">
            {rawImage && (
              <Cropper
                image={rawImage}
                crop={crop}
                zoom={zoom}
                aspect={1}
                onCropChange={setCrop}
                onZoomChange={setZoom}
                onCropComplete={onCropComplete}
                cropShape="round"
                showGrid={false}
              />
            )}
          </div>

          <div className="flex items-center gap-3 px-1">
            <span className="text-xs text-muted-foreground shrink-0">Zoom</span>
            <Slider
              min={1}
              max={3}
              step={0.05}
              value={[zoom]}
              onValueChange={(v) => setZoom(v[0])}
              className="flex-1"
            />
          </div>

          <DialogFooter className="flex-row gap-2 sm:justify-between">
            <div>
              {onDelete && imageUrl && (
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={async () => {
                    setIsUploading(true);
                    try {
                      await onDelete();
                      setDialogOpen(false);
                      setRawImage(null);
                    } catch {
                      // handled in onDelete
                    } finally {
                      setIsUploading(false);
                    }
                  }}
                  disabled={isUploading}
                >
                  <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                  Remove
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                disabled={isUploading}
              >
                Cancel
              </Button>
              <Button
                type="button"
                onClick={handleConfirmCrop}
                disabled={isUploading || !croppedArea}
              >
                {isUploading && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Save
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
